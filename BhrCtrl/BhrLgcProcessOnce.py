import sys
import os
import pandas as pd
import numpy as np
import json
import re
import pickle
import hashlib
import configparser
import yaml
import traceback

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

config = configparser.ConfigParser()
# Adjust path to look for config.ini in AImodule regardless of the current directory
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)

yaml_path = os.path.join(base_dir, 'char_config.yaml')

# Load the YAML file
with open(yaml_path, 'r') as file:
    char_config = yaml.safe_load(file)
    print("YAML content loaded successfully.")

def processOneInputGiveOneInstruction():
    """
    Process one input from the Java buffer and generate one instruction for the NPC.
    """
    try:
        db_conn = DBCon.establish_sql_connection()
        input_from_java = BhrDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)

        if input_from_java is None:
            print('Nothing to process so far')
            return 0

        request_id = input_from_java[0]
        curTime = input_from_java[1]
        npcId = input_from_java[2]
        java_json = input_from_java[3]

        print("Processing Request Id: ", request_id)

        # Parse talking and idling info
        talkingInfo, is_talking = BhrLgcManualProcess.parse_talking_from_java(java_json)
        is_idling = BhrLgcManualProcess.parse_isIdling(java_json)

        # Parse NPC info for next action
        inputInHumanString = BhrLgcManualProcess.parse_npc_info_for_nextaction(java_json)

        # Get relevant memories
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

            rows_df['cosine_similarity'] = rows_df['Embedding'].apply(
                lambda x: cosine_similarity(BufferRowEmbedding, np.array(x))
            )

            # Adjusting weights for retrieval score
            a_recency = 0.2
            a_importance = 0.2
            a_similarity = 0.6

            rows_df['retrieval_score'] = (
                a_recency * rows_df['recency'] +
                a_importance * rows_df['Importance'] +
                a_similarity * rows_df['cosine_similarity']
            )

            rows_df_ranked = rows_df.sort_values(
                by=['retrieval_score', 'Time'], ascending=[False, False]
            ).head(30)
            rows_df_ranked = rows_df_ranked.sort_values(by='Time', ascending=False)
            paragraph = "\n".join(rows_df_ranked['Content'].astype(str).tolist())
            memories_str = paragraph
        else:
            memories_str = 'No memory yet'

        if memories_str == '':
            memories_str = 'No memory yet'

        print('Relevent Memories:')
        print(memories_str)
        print()

        # Retrieve latest reflection
        prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, curTime)
        if prior_reflection is not None:
            prior_reflection_str = str(prior_reflection[2])
        else:
            prior_reflection_str = 'No prior reflection yet!'

        print('Prior Reflection:')
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
            cur_schedule_str = npc['schedule']

        instruction_in_human = ''

        # Check states: finding people to talk, idling, talking, buying
        is_findingToTalk, targetNPCId = BhrLgcManualProcess.parse_isFindingPeopletoTalk(java_json)
        is_idling = BhrLgcManualProcess.parse_isIdling(java_json)
        is_talking = BhrLgcManualProcess.parse_isTalking(java_json)
        is_buying, shopownerNPCId = BhrLgcManualProcess.parse_isBuying(java_json)

        is_talk_instruction = False

        # Determine next action based on current states
        if is_findingToTalk:
            target_sleeping, sleep_target_name = BhrLgcManualProcess.parse_target_sleeping(java_json)
            target_talking, talk_target_name = BhrLgcManualProcess.parse_target_talking(java_json)

            if target_sleeping or target_talking:
                instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
                )
            else:
                instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, targetNPCId
                )
                is_talk_instruction = True

        elif is_buying:
            shop_target_present, shopowner_target_name = BhrLgcManualProcess.parse_target_oid_owner_at_shop(java_json)

            if not shop_target_present:
                instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
                )
            else:
                instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, shopownerNPCId
                )
                is_talk_instruction = True

        elif is_talking:
            instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk
            )
            is_talk_instruction = True

        elif is_idling:
            instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
            )

        # Generate final instruction JSON
        if instruction_in_human != '':
            retry = 0
            while retry < 3:
                try:
                    instruction_to_give = BhrLgcGPTProcess.humanInstToJava_action(
                        instruction_in_human, "", npcId
                    ).strip("```json").strip("```")
                    instruction_json = json.loads(instruction_to_give)
                    instruction_json['requestId'] = request_id
                    instruction_to_give = json.dumps(instruction_json)
                    break
                except Exception as e:
                    retry += 1
                    if retry == 3:
                        return 0

            print('Instruction to give:')
            print(instruction_json)
            print()

            BhrDBInstruction.insert_into_instruction_table(db_conn, curTime, npcId, instruction_to_give, request_id)

        BhrDBJavaBuffer.mark_entry_as_processed(db_conn, request_id)

        return 1

    except Exception as e:
        traceback.print_exc()
        return 0