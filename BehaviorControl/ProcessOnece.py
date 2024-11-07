import sys
import os
sys.path.append('../DBmanipulation')

import DBCon 
import BufferDB
import InstructionDB
import ReflectionTracerDB
import MemStreDB
import ReflectionDB
# import ScheduleDB

import GPTProcess
import ManualProcess
import InstToMemStre
import InputToMemStre



import pandas as pd
import numpy as np
import json
import re
import pickle


def processOneInputGiveOneInstruction():
    instruction_db_conn = schedule_db_conn = buffer_db_conn = reflection_tracer_db_conn = reflection_db_conne = memstre_db_conn = buffer_db_conn= DBCon.establish_sql_connection()
    input_from_java = BufferDB.get_earliest_unprocessed_entry(buffer_db_conn)
    print(input_from_java)

    if input_from_java is None:
        print('Nothing to process so far')
        print()
        print()
        return 0

    npcId = input_from_java[1]
    AllEntryOfNPC, LatestEntryOfNpc = BufferDB.get_unprocessed_entries_of_npc(buffer_db_conn, npcId)
    input_from_java = LatestEntryOfNpc



    curTime = input_from_java[0]
    inputInHumanString = ManualProcess.parse_npc_info(input_from_java[2])



  # Get Relavent Memeory from Memeory Stream
    BufferRowEmbedding = GPTProcess.get_embedding(inputInHumanString)
    rows_df = MemStreDB.retrieve_most_recent_entries(memstre_db_conn, npcId, curTime)
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

        a_recency = 0.5  # Adjust the weight for recency as needed
        a_importance = 0.3  # Adjust the weight for importance as needed
        a_similarity = 0.2  # Adjust the weight for similarity as needed


        rows_df['retrieval_score'] = (
            a_recency * rows_df['recency'] +
            a_importance * rows_df['Importance'] + 
            a_similarity * rows_df['cosine_similarity']
        )

        rows_df_ranked = rows_df.sort_values(by=['retrieval_score', 'Time'], ascending=[False, False]).head(20)
        rows_df_ranked = rows_df_ranked.sort_values(by='Time', ascending=False)
        rows_df_ranked
        # memories_str = str(list(rows_df_ranked['Content']))
        paragraph = " ".join(rows_df_ranked['Content'].astype(str).tolist())
        memories_str = paragraph
    else:
        memories_str = 'No memory yet'



    #Retrive latest reflection
    prior_reflection = ReflectionDB.retrieve_last_entry_before_time(reflection_db_conne, npcId, curTime)
    if prior_reflection is not None:
        prior_reflection_str = str(prior_reflection[2])
    else:
        prior_reflection_str = 'No prior reflection yet!'

    
    # Process these information 
    instruction_in_human = GPTProcess.process_all_give_conversation(memories_str, prior_reflection_str, inputInHumanString, 'Be dramatic, no emoji, under 140 characters')# Translate to instruction 
    # Translate to instruction
    instruction_to_give = ManualProcess.talkingInstruction(npcId, instruction_in_human)

    # Mark the buffer as processed
    BufferDB.mark_entry_as_processed(buffer_db_conn, curTime, npcId)
    for row in AllEntryOfNPC:
        time_to_mark = row[0]
        npcId_to_mark = row[1]
        BufferDB.mark_entry_as_processed(buffer_db_conn, time_to_mark, npcId_to_mark)
        
    # add to instruction db
    # print()
    # print()
    # print()
    # print(curTime)
    # print(npcId)
    # print(instruction_to_give)
    # print()
    # print()
    # print()
    # print()
    InstructionDB.insert_into_instruction_table(instruction_db_conn, curTime, npcId, instruction_to_give)
    
    

    # insert instruction to Memory Stream
    InstToMemStre.InstToMemStreSatoshiDB(input_from_java, instruction_in_human)
    # add importance to Reflection Tracer
    InstToMemStre.InstImportancetoReflectionTracer( input_from_java, instruction_to_give, instruction_in_human)
    print(instruction_to_give)

    # Generate Reflection if needed
    npcId = input_from_java[1]
    curTime = input_from_java[0]
    output = ReflectionTracerDB.retrieve_entry(reflection_tracer_db_conn, npcId)
    if output:
        output_importance, output_starttime, output_endtime = output[0], output[1], output[2]
        if output_importance > 30:
            #TODO: Generate reflection, and add to DB
            memstrm_db_conn = DBCon.establish_sql_connection()
            memories = MemStreDB.retrieve_entries_between_time(memstrm_db_conn, npcId, output_starttime, output_endtime)
            reflection_db_con = DBCon.establish_sql_connection()
            prior_reflection = ReflectionDB.retrieve_last_entry_before_time(reflection_db_con, npcId, output_endtime)
            if prior_reflection is not None:
                prior_reflection_str = prior_reflection[2]
            else:
                prior_reflection_str = ''
            if memories is not None:
                memories_str = str(memories['Content'])
            else:
                memories_str = ''
            new_reflection = GPTProcess.generate_reflection(prior_reflection_str, memories_str,inputInHumanString)
            ReflectionDB.insert_into_table(reflection_db_con, npcId, curTime, new_reflection)
            #Reset the importance tracer
            ReflectionTracerDB.insert_into_table(reflection_tracer_db_conn, npcId, 0, curTime, curTime)
    

    return 1