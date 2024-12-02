import sys
import os

import DBConnect.DBCon as DBCon
import DBConnect.DBCon as DBCon 

from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule

import BhrLgcGPTProcess
import BhrLgcManualProcess
import BhrCtrl.BhrLgcToMemStre as BhrLgcToMemStre
import BhrLgcToMemStre

import pandas as pd
import numpy as np
import json
import re
import pickle
import hashlib

def processOneInputGiveOneInstruction():
    db_conn = DBCon.establish_sql_connection()
    input_from_java = BhrDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)
    
    if input_from_java is None:
        print('Nothing to process so far')
        return 0
    else:
        print('Processing the following input:')
        print(input_from_java)

    npcId = input_from_java[2]
    # AllEntryOfNPC, LatestEntryOfNpc = BhrDBJavaBuffer.get_unprocessed_entries_of_npc(db_conn, npcId)
    # input_from_java = LatestEntryOfNpc

    curTime = input_from_java[1]
    request_id = input_from_java[0]
    inputInHumanString = BhrLgcManualProcess.parse_npc_info(input_from_java[3])

    # Get Relevant Memory from Memory Stream
    BufferRowEmbedding = BhrLgcGPTProcess.get_embedding(inputInHumanString)
    rows_df = BhrDBMemStre.retrieve_most_recent_entries(db_conn, npcId, curTime)
    if rows_df is not None:
        rows_df['Time'] = pd.to_datetime(rows_df['Time'])
        rows_df['TimeDifference'] = (rows_df['Time'] - pd.to_datetime(curTime)).dt.total_seconds()
        decay_rate = 0.001 
        rows_df['recency'] = np.exp(decay_rate * rows_df['TimeDifference'])

        def cosine_similarity(vec1, vec2):
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            return dot_product / (norm_vec1 * norm_vec2)

        rows_df['cosine_similarity'] = rows_df['Embedding'].apply(lambda x: cosine_similarity(BufferRowEmbedding, np.array(x)))

        a_recency = 0.2  # Adjust the weight for recency as needed
        a_importance = 0.2  # Adjust the weight for importance as needed
        a_similarity = 0.6  # Adjust the weight for similarity as needed

        rows_df['retrieval_score'] = (
            a_recency * rows_df['recency'] +
            a_importance * rows_df['Importance'] + 
            a_similarity * rows_df['cosine_similarity']
        )

        rows_df_ranked = rows_df.sort_values(by=['retrieval_score', 'Time'], ascending=[False, False]).head(20)
        rows_df_ranked = rows_df_ranked.sort_values(by='Time', ascending=False)
        paragraph = " ".join(rows_df_ranked['Content'].astype(str).tolist())
        memories_str = paragraph
    else:
        memories_str = 'No memory yet'
    if memories_str == '':
        memories_str = 'No memory yet'
    print('Memories:')
    print(memories_str)
    print()

    # Retrieve latest reflection
    prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, curTime)
    if prior_reflection is not None:
        prior_reflection_str = str(prior_reflection[2])
    elif prior_reflection == "None":
        prior_reflection_str = 'No prior reflection yet!'
    else:
        prior_reflection_str = 'No prior reflection yet!'
    
    # print( 'Prior Reflection not str:')
    # print(prior_reflection)
    print( 'Prior Reflection:')
    print(prior_reflection_str)
    print()

    # Retrieve latest Schedule
    cur_schedule = BhrDBSchedule.retrieve_latest_schedule(db_conn, npcId)
    if cur_schedule is not None:
        cur_schedule_str = str(cur_schedule['schedule'])
    else:
        cur_schedule_str = 'No schedule yet!'

    # Generate New Schedule if needed
    if BhrLgcGPTProcess.need_new_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId):
        cur_schedule_str = BhrLgcGPTProcess.generate_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId)
        BhrDBSchedule.insert_into_table(db_conn, npcId, curTime, cur_schedule_str)
    print('Current Schedule:')
    print(cur_schedule)
    print()

    
    # Process this information, and give instruction in human language
    instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
        memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
    )

    # Generate sentences for the NPC to say during the action
    if BhrLgcGPTProcess.needDeepTalk(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId):
        theme_for_generation = BhrLgcGPTProcess.generateTheme(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId, special_instruction='')
        words_to_say = BhrLgcGPTProcess.generate_new_Announcement(memories_str, prior_reflection_str, theme_for_generation, npcId)
    else:
        words_to_say = BhrLgcGPTProcess.generateThreeSentencesForAction(memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId)

    while True:
        try:
            # Convert the instruction into JSON format
            instruction_to_give = BhrLgcGPTProcess.humanInstToJava(instruction_in_human, words_to_say).strip("```json").strip("```")
            # Parse the instruction into a JSON object
            instruction_json = json.loads(instruction_to_give)
            
            # If no error occurs, break the loop
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying...")

    # instruction_to_give = BhrLgcGPTProcess.humanInstToJava(instruction_in_human, words_to_say).strip("```json").strip("```")
    # print()
    # print(print(instruction_to_give))
    # print()
    # # Parse the instruction into a JSON object
    # instruction_json = json.loads(instruction_to_give)

            

    # Add unique ack
    
    # print(type(instruction_json))
    # print(instruction_json)
    # instruction_json['ack'] = hashlib.sha256(instruction_to_give.encode('utf-8')).hexdigest()
    print('Instruction to give:')
    print(instruction_json)
    print()

    # Add to instruction db
    BhrDBInstruction.insert_into_instruction_table(db_conn, curTime, npcId, instruction_to_give)

    # Mark the buffer as processed
    BhrDBJavaBuffer.mark_entry_as_processed(db_conn, request_id)
    # for row in AllEntryOfNPC:
    #     request_id_to_mark = row[0]
    #     BhrDBJavaBuffer.mark_entry_as_processed(db_conn, request_id_to_mark)

    # Insert Input to Memory Stream, only talk needs to be inserted for now.
    
    data = json.loads(input_from_java[3])
    npcs = data.get('npcs', [])
    if len(npcs) > 0:
        npc = npcs[0]  
        talk_info = npc.get('talk', {})
        is_talking = talk_info.get('isTalking', False)
        if is_talking:
            input_for_mem = BhrLgcManualProcess.parse_npc_info_formemory(input_from_java[3])
            BhrLgcToMemStre.InputToMemStreDB(input_from_java, input_for_mem)
            BhrLgcToMemStre.InstImportancetoReflectionTracer(input_from_java, input_for_mem)
        
    # Insert instruction to Memory Stream
    BhrLgcToMemStre.InstToMemStreDB(input_from_java, "At "+str(curTime) + " ," + instruction_in_human)
    BhrLgcToMemStre.InstImportancetoReflectionTracer(input_from_java, instruction_in_human)

    # Generate reflection if needed
    # npcId = input_from_java[1]
    # curTime = input_from_java[0]
    output = BhrDBReflectionTracer.retrieve_entry(db_conn, npcId)
    # print('Refelction Tracer Output: ', output)
    if output:
        output_importance, output_starttime, output_endtime = output[0], output[1], output[2]
        # print('Total Importance: ', output_importance)
        if output_importance > 30:
            # print('Now is reflection time')

            memories = BhrDBMemStre.retrieve_entries_between_time(db_conn, npcId, output_starttime, output_endtime)
            prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, output_endtime)
            prior_reflection_str = prior_reflection[2] if prior_reflection is not None else 'No prior reflections'
            memories_str = str(memories['Content']) if memories is not None else 'No prior memeories'

            # print('This is prior memeories for reflection: ', memories)
            # print('This is prior reflection for reflection: ', prior_reflection_str)
            
            new_reflection = BhrLgcGPTProcess.generate_reflection_new(prior_reflection_str, memories_str, inputInHumanString, npcId)
            print("New Reflection: ", new_reflection)

            BhrDBReflection.insert_into_table(db_conn, npcId, curTime, new_reflection)
            # Reset the importance tracer
            BhrDBReflectionTracer.insert_into_table(db_conn, npcId, 0, curTime, curTime)
            # print('insert in to relative tables')


    return 1