import sys
import os
# Add the base directory (one level up from the current directory)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

from DBConnect import DBCon
from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule

import BhrLgcGPTProcess
import BhrLgcManualProcess
import BhrLgcToMemStre

import pandas as pd
import numpy as np
import json
import re
import pickle
import hashlib
import configparser
import yaml

config = configparser.ConfigParser()
# Adjust path to look for config.ini in AImodule regardless of the current directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)

yaml_path = os.path.join(base_dir, 'char_config.yaml')

# Load the YAML file

with open(yaml_path, 'r') as file:
    char_config = yaml.safe_load(file)
    print("YAML content loaded successfully.")


def processOneInputGiveOneInstruction():
    db_conn = DBCon.establish_sql_connection()
    input_from_java = BhrDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)
    
    if input_from_java is None:
        print('Nothing to process so far')
        return 0
    else:
        print('Processing the following input:')
        print(input_from_java)

    request_id = input_from_java[0]
    curTime = input_from_java[1]
    npcId = input_from_java[2]

    print("Processing Request Id: ", request_id)

    java_json = input_from_java[3]
    talkingInfo, is_talking = BhrLgcManualProcess.parse_talking_from_java(java_json)
    is_idling = BhrLgcManualProcess.parse_isIdling(java_json)
    

    inputInHumanString = BhrLgcManualProcess.parse_npc_info_for_nextaction(java_json)

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

        rows_df_ranked = rows_df.sort_values(by=['retrieval_score', 'Time'], ascending=[False, False]).head(30)
        rows_df_ranked = rows_df_ranked.sort_values(by='Time', ascending=False)
        paragraph = "\n".join(rows_df_ranked['Content'].astype(str).tolist())
        memories_str = paragraph
    else:
        memories_str = 'No memory yet'
    if memories_str == '':
        memories_str = 'No memory yet'
    print('Relevent Memeories:')
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
    
    print( 'Prior Reflection:')
    print(prior_reflection_str)
    print()

    # Retrieve latest Schedule
    cur_schedule = BhrDBSchedule.retrieve_latest_schedule(db_conn, npcId)
    if cur_schedule is not None:
        cur_schedule_str = str(cur_schedule['schedule'])
    else:
        npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
        if not npc:
            raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")
        cur_schedule_str =  npc['schedule']

    
    is_findingToTalk = BhrLgcManualProcess.parse_isFindingPeopletoTalk(java_json) # Last action is finding people to talk
    is_idling = BhrLgcManualProcess.parse_isIdling(java_json)
    is_talking = BhrLgcManualProcess.parse_isTalking(java_json) 
    is_buying = BhrLgcManualProcess.parse_isBuying(java_json)
    is_talk_instruction = False

    if is_findingToTalk:
        print ('Last action is finding people to talk, next action should be talking')
        target_sleeping, sleep_target_name = BhrLgcManualProcess.parse_target_sleeping(java_json) 
        target_talking, talk_target_name = BhrLgcManualProcess.parse_target_talking(java_json)
        if target_sleeping or target_talking:
            # action: move, npcid 这个人，在surrounding 睡觉，做下个动作，npc在睡觉进memeories
            print('I am going to find someone to talk to, and that person is sleeping or is talking now')
            instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId)
            if BhrLgcGPTProcess.needDeepTalk(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId):
                theme_for_generation = BhrLgcGPTProcess.generateTheme(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId, special_instruction='')
                words_to_say = BhrLgcGPTProcess.generate_new_Announcement(memories_str, prior_reflection_str, theme_for_generation, npcId)
            else:
                words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId)
            target_name = 'Cannot find target'
            if sleep_target_name:
                target_name = sleep_target_name
            elif talk_target_name:
                target_name = talk_target_name
            instruction_in_human += f" I went to the {target_name} but he is sleeping, I am going to do something else now."
            is_talk_instruction = False
        else:
            print('Start Talking to the the person')
            instruction_in_human = BhrLgcGPTProcess.talkToSomeone(memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk)
            words_to_say = ''
            is_talk_instruction = True
    elif is_buying:
        print ('I am buying something, next action should be talking for buying stuff')
        #  buying case, action: move, npcid 这个人，在surrounding 买东西，做下个动作，npc在买东西进memeories
        shop_target_present, shopowner_target_name  = BhrLgcManualProcess.parse_target_oid_owner_at_shop(java_json)
        if not shop_target_present:
            # TODO: action: move, npcid 这个人，不在surranding或卖东西，做下个动作，npc在睡觉进memeories
            print('I am going to buy something, and the shop onwer is not their')
            instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId)
            if BhrLgcGPTProcess.needDeepTalk(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId):
                theme_for_generation = BhrLgcGPTProcess.generateTheme(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId, special_instruction='')
                words_to_say = BhrLgcGPTProcess.generate_new_Announcement(memories_str, prior_reflection_str, theme_for_generation, npcId)
            else:
                words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId)
            instruction_in_human += f" I went to the {shopowner_target_name}'s store to buy but he is not there, purchase failed, I am going to do something else now."
            is_talk_instruction = False
        else:
            print('Start Talking to the shop owner')
            instruction_in_human = BhrLgcGPTProcess.talkToSomeone(memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk)
            words_to_say = ''
            is_talk_instruction = True
    elif is_talking: # This case, the NPC is talking to someone and doing his/her own business
        instruction_in_human = BhrLgcGPTProcess.talkToSomeone(memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk)
        words_to_say = ''
        is_talk_instruction = True
    elif is_idling:
        print ('Is idling,next action')
        # Next action
        instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId)
        # Generate sentences for the NPC to say during the action
        if BhrLgcGPTProcess.needDeepTalk(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId):
            theme_for_generation = BhrLgcGPTProcess.generateTheme(memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId, special_instruction='')
            words_to_say = BhrLgcGPTProcess.generate_new_Announcement(memories_str, prior_reflection_str, theme_for_generation, npcId)
        else:
            words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId)
        is_talk_instruction = False
 
    
        
    if instruction_in_human != '':
        if is_talk_instruction:
            while True:
                try:
                    instruction_to_give = BhrLgcGPTProcess.humanInstToJava_talk(instruction_in_human, words_to_say, npcId).strip("```json").strip("```")
                    instruction_json = json.loads(instruction_to_give)
                    instruction_json['requestId'] = request_id
                    break
                except Exception as e:
                    print(f"Error occurred: {e}. Retrying...")
        else:
            while True:
                    try:
                        instruction_to_give = BhrLgcGPTProcess.humanInstToJava_action(instruction_in_human, words_to_say, npcId).strip("```json").strip("```")
                        instruction_json = json.loads(instruction_to_give)
                        instruction_json['requestId'] = request_id
                        break
                    except Exception as e:
                        print(f"Error occurred: {e}. Retrying...")


        print('Instruction to give:')
        print(instruction_json)
        print()
        # Add to instruction db
        BhrDBInstruction.insert_into_instruction_table(db_conn, curTime, npcId, instruction_to_give, request_id)

    # Mark the buffer as processed
    BhrDBJavaBuffer.mark_entry_as_processed(db_conn, request_id)

    # Only do so if there is an instruction to give
    if instruction_in_human != '':
        # Insert the java input into the instruction table
        # Generate New Schedule if needed
        if BhrLgcGPTProcess.need_new_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId):
            cur_schedule_str = BhrLgcGPTProcess.generate_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId)
            BhrDBSchedule.insert_into_table(db_conn, npcId, curTime, cur_schedule_str)
        print('Current Schedule:')
        print(cur_schedule)
        print()
    
        data = json.loads(java_json)
        npcs = data.get('npcs', [])
        if len(npcs) > 0:
            npc = npcs[0]  
            talk_info = npc.get('talk', {})
            is_talking = talk_info.get('isTalking', False)
            if is_talking:
                input_for_mem = BhrLgcManualProcess.parse_npc_info_formemory(java_json)
                BhrLgcToMemStre.InputToMemStreDB(input_from_java, input_for_mem)
                BhrLgcToMemStre.InstImportancetoReflectionTracer(input_from_java, input_for_mem)

        # Insert instruction to Memory Stream
        BhrLgcToMemStre.InstToMemStreDB(input_from_java, "At "+str(curTime) + " ," + instruction_in_human)
        BhrLgcToMemStre.InstImportancetoReflectionTracer(input_from_java, instruction_in_human)


        output = BhrDBReflectionTracer.retrieve_entry(db_conn, npcId)
        # print('Refelction Tracer Output: ', output)
        if output:
            output_importance, output_starttime, output_endtime = output[0], output[1], output[2]
            # print('Total Importance: ', output_importance)
            if output_importance > 100:
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