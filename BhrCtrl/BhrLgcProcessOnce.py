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
import BhrLgcInstToMemStre
import BhrLgcInputToMemStre

import pandas as pd
import numpy as np
import json
import re
import pickle
import hashlib

def processOneInputGiveOneInstruction():
    db_conn = DBCon.establish_sql_connection()
    input_from_java = BhrDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)
    print(input_from_java)

    if input_from_java is None:
        print('Nothing to process so far')
        print()
        print()
        return 0

    npcId = input_from_java[1]
    AllEntryOfNPC, LatestEntryOfNpc = BhrDBJavaBuffer.get_unprocessed_entries_of_npc(db_conn, npcId)
    input_from_java = LatestEntryOfNpc

    curTime = input_from_java[0]
    inputInHumanString = BhrLgcManualProcess.parse_npc_info(input_from_java[2])

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

    # Retrieve latest reflection
    prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, curTime)
    if prior_reflection is not None:
        prior_reflection_str = str(prior_reflection[2])
    else:
        prior_reflection_str = 'No prior reflection yet!'

    # Retrive latest Schedule
    cur_schedule = BhrDBSchedule.retrieve_latest_schedule(db_conn, npcId)
    if cur_schedule is not None:
        cur_schedule_str = str(cur_schedule[2])
    else:
        cur_schedule_str = 'No schedule yet!'

    # Generate New Schedule if needed
    if BhrLgcGPTProcess.need_new_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString):
        cur_schedule_str = BhrLgcGPTProcess.generate_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString)
        BhrDBSchedule.insert_into_table(db_conn, npcId, curTime, cur_schedule_str)
    

    # Process this information, and give instruction in human language
    
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString)
            words_to_say = BhrLgcGPTProcess.generateThreeSentencesForAction(memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human)
            instruction_to_give = BhrLgcGPTProcess.humanInstToJava(npcId, words_to_say).strip("```json").strip("```")
            instruction_json = json.loads(instruction_to_give)
        except Exception as e:
            # Log the error and increment retries
            print(f"Attempt {retries + 1} failed: {e}")
            retries += 1
    # Raise an exception if max retries are exceeded
    raise Exception(f"Failed to generate valid JSON after {max_retries} attempts.")

    # Add unique ack,
    instruction_json['ack'] = hashlib.sha256(instruction_to_give.encode('utf-8')).hexdigest()
    

    # Add to instruction db
    BhrDBInstruction.insert_into_instruction_table(db_conn, curTime, npcId, instruction_to_give)

    # Mark the buffer as processed
    BhrDBJavaBuffer.mark_entry_as_processed(db_conn, curTime, npcId)
    for row in AllEntryOfNPC:
        time_to_mark = row[0]
        npcId_to_mark = row[1]
        BhrDBJavaBuffer.mark_entry_as_processed(db_conn, time_to_mark, npcId_to_mark)
        
    # Insert instruction to Memory Stream
    BhrLgcInstToMemStre.InstToMemStreSatoshiDB(input_from_java, instruction_in_human)
    BhrLgcInstToMemStre.InstImportancetoReflectionTracer(input_from_java, instruction_to_give, instruction_in_human)
    print(instruction_to_give)

    # Generate reflection if needed
    npcId = input_from_java[1]
    curTime = input_from_java[0]
    output = BhrDBReflectionTracer.retrieve_entry(db_conn, npcId)
    if output:
        output_importance, output_starttime, output_endtime = output[0], output[1], output[2]
        if output_importance > 30:
            memories = BhrDBMemStre.retrieve_entries_between_time(db_conn, npcId, output_starttime, output_endtime)
            prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, output_endtime)
            prior_reflection_str = prior_reflection[2] if prior_reflection is not None else ''
            memories_str = str(memories['Content']) if memories is not None else ''
            new_reflection = BhrLgcGPTProcess.generate_reflection(prior_reflection_str, memories_str, inputInHumanString)
            BhrDBReflection.insert_into_table(db_conn, npcId, curTime, new_reflection)
            # Reset the importance tracer
            BhrDBReflectionTracer.insert_into_table(db_conn, npcId, 0, curTime, curTime)

    return 1