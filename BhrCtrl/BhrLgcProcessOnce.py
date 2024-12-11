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
import logging
from datetime import datetime

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
with open(yaml_path, 'r', encoding='utf-8') as file:
    char_config = yaml.safe_load(file)
    print("YAML content loaded successfully.")

# Setup a logger
def setup_logger(request_id):
    logger = logging.getLogger(f"Logger_{request_id}")
    logger.setLevel(logging.DEBUG)
    
    # Prevent adding multiple handlers to the logger
    if not logger.handlers:
        # Create a directory for log files if it doesn't exist
        log_dir = os.path.join(base_dir, 'BhrCtrl', 'printout')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file_path = os.path.join(log_dir, f"{request_id}.log")
        
        # Create file handler which logs even debug messages
        fh = logging.FileHandler(log_file_path, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(fh)
    
    return logger

def processOneInputGiveOneInstruction():
    """
    Process one input from the Java buffer and generate one instruction for the NPC.
    """
    logger = None  # Initialize logger variable
    try:
        db_conn = DBCon.establish_sql_connection()
        input_from_java = BhrDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)

        if input_from_java is None:
            print('Nothing to process so far')
            return 0
        else:
            request_id = input_from_java[0]
            logger = setup_logger(request_id)

            logger.info('Processing the following input:')
            logger.info(input_from_java)

            curTime = input_from_java[1]
            npcId = input_from_java[2]
            java_json = input_from_java[3]

            logger.info(f"Processing Request Id: {request_id}")

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
                    if norm_vec1 == 0 or norm_vec2 == 0:
                        return 0.0
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

            logger.info('Relevant Memories:')
            logger.info(memories_str)
            logger.info("")  # Logging an empty line for readability

            # Retrieve latest reflection
            prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, curTime)
            if prior_reflection is not None:
                prior_reflection_str = str(prior_reflection[2])
            else:
                prior_reflection_str = 'No prior reflection yet!'

            logger.info('Prior Reflection:')
            logger.info(prior_reflection_str)
            logger.info("")

            # Retrieve latest Schedule
            cur_schedule = BhrDBSchedule.retrieve_latest_schedule(db_conn, npcId)
            if cur_schedule is not None:
                cur_schedule_str = str(cur_schedule['schedule'])
            else:
                # If no schedule is found in DB, fallback to char_config.yaml
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
                logger.info('Last action is finding people to talk, next action should be talking')
                target_sleeping, sleep_target_name = BhrLgcManualProcess.parse_target_sleeping(java_json)
                target_talking, talk_target_name = BhrLgcManualProcess.parse_target_talking(java_json)

                if target_sleeping or target_talking:
                    # Target is not available for conversation
                    logger.info('Target is sleeping or talking, choose another action')
                    instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                        memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
                    )
                    if BhrLgcGPTProcess.needDeepTalk(
                        memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                    ):
                        theme_for_generation = BhrLgcGPTProcess.generateTheme(
                            memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                        )
                        words_to_say = BhrLgcGPTProcess.generate_new_Announcement(
                            memories_str, prior_reflection_str, theme_for_generation, npcId
                        )
                    else:
                        words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(
                            memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId
                        )
                    target_name = sleep_target_name if sleep_target_name else (talk_target_name if talk_target_name else 'Unknown')
                    instruction_in_human += f" I went to the {target_name} but they are not available, going to do something else now."
                    is_talk_instruction = False
                else:
                    logger.info('Start Talking to the person')
                    instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                        memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, targetNPCId
                    )
                    words_to_say = ''
                    is_talk_instruction = True

            elif is_buying:
                logger.info('I am buying something, next action should be talking for buying stuff')
                shop_target_present, shopowner_target_name = BhrLgcManualProcess.parse_target_oid_owner_at_shop(java_json)

                if not shop_target_present:
                    # Shop owner not present
                    logger.info('Shop owner not present, choose another action')
                    instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                        memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
                    )
                    if BhrLgcGPTProcess.needDeepTalk(
                        memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                    ):
                        theme_for_generation = BhrLgcGPTProcess.generateTheme(
                            memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                        )
                        words_to_say = BhrLgcGPTProcess.generate_new_Announcement(
                            memories_str, prior_reflection_str, theme_for_generation, npcId
                        )
                    else:
                        words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(
                            memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId
                        )
                    instruction_in_human += f" I went to {shopowner_target_name}'s store to buy but they are not there, purchase failed, doing something else now."
                    is_talk_instruction = False
                else:
                    logger.info('Start Talking to the shop owner')
                    instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                        memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk, shopownerNPCId
                    )
                    words_to_say = ''
                    is_talk_instruction = True

            elif is_talking:
                # NPC currently talking
                instruction_in_human = BhrLgcGPTProcess.talkToSomeone(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId, is_findingToTalk
                )
                words_to_say = ''
                is_talk_instruction = True

            elif is_idling:
                # NPC is idling, decide next action
                logger.info('Is idling, decide next action')
                instruction_in_human = BhrLgcGPTProcess.processInputGiveWhatToDo(
                    memories_str, prior_reflection_str, cur_schedule_str, inputInHumanString, npcId
                )
                if BhrLgcGPTProcess.needDeepTalk(
                    memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                ):
                    theme_for_generation = BhrLgcGPTProcess.generateTheme(
                        memories_str, prior_reflection_str, inputInHumanString, instruction_in_human, npcId
                    )
                    words_to_say = BhrLgcGPTProcess.generate_new_Announcement(
                        memories_str, prior_reflection_str, theme_for_generation, npcId
                    )
                else:
                    words_to_say = BhrLgcGPTProcess.generateMultipleSentencesForAction(
                        memories_str, prior_reflection_str, cur_schedule_str, instruction_in_human, npcId
                    )
                is_talk_instruction = False

            # Generate final instruction JSON
            if instruction_in_human != '':
                if is_talk_instruction:
                    retry = 0
                    while retry < 3:
                        try:
                            instruction_to_give = BhrLgcGPTProcess.humanInstToJava_talk(
                                instruction_in_human, words_to_say, npcId
                            ).strip("```json").strip("```")
                            instruction_json = json.loads(instruction_to_give)
                            instruction_json['requestId'] = request_id
                            # Re-serialize the JSON after adding requestId
                            instruction_to_give = json.dumps(instruction_json, ensure_ascii=False)
                            break
                        except Exception as e:
                            logger.error(f"Error occurred: {e}. Retrying...", exc_info=True)
                            retry += 1
                            if retry == 3:
                                return 0
                else:
                    retry = 0
                    while retry < 3:
                        try:
                            instruction_to_give = BhrLgcGPTProcess.humanInstToJava_action(
                                instruction_in_human, words_to_say, npcId
                            ).strip("```json").strip("```")
                            instruction_json = json.loads(instruction_to_give)
                            instruction_json['requestId'] = request_id
                            # Re-serialize after adding requestId
                            instruction_to_give = json.dumps(instruction_json, ensure_ascii=False)
                            break
                        except Exception as e:
                            logger.error(f"Error occurred: {e}. Retrying...", exc_info=True)
                            retry += 1
                            if retry == 3:
                                return 0

                logger.info('Instruction to give:')
                logger.info(instruction_json)
                logger.info("")  # Corrected from logger.info()

                # Add to instruction db
                BhrDBInstruction.insert_into_instruction_table(db_conn, curTime, npcId, instruction_to_give, request_id)

            # Mark the buffer as processed
            BhrDBJavaBuffer.mark_entry_as_processed(db_conn, request_id)

            # If we produced an instruction
            if instruction_in_human != '':
                # Check if a new schedule is needed
                if BhrLgcGPTProcess.need_new_schedule(cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId):
                    cur_schedule_str = BhrLgcGPTProcess.generate_schedule(
                        cur_schedule_str, memories_str, prior_reflection_str, inputInHumanString, npcId
                    )
                    BhrDBSchedule.insert_into_table(db_conn, npcId, curTime, cur_schedule_str)

                logger.info('Current Schedule:')
                logger.info(cur_schedule_str)
                logger.info("")  # Corrected from logger.info()

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
                BhrLgcToMemStre.InstToMemStreDB(input_from_java, f"At {curTime}, {instruction_in_human}")
                BhrLgcToMemStre.InstImportancetoReflectionTracer(input_from_java, instruction_in_human)

                # Check reflection importance
                output = BhrDBReflectionTracer.retrieve_entry(db_conn, npcId)
                if output:
                    output_importance, output_starttime, output_endtime = output[0], output[1], output[2]
                    if output_importance > 100:
                        # Time for reflection
                        memories = BhrDBMemStre.retrieve_entries_between_time(db_conn, npcId, output_starttime, output_endtime)
                        prior_reflection = BhrDBReflection.retrieve_last_entry_before_time(db_conn, npcId, output_endtime)
                        if prior_reflection is not None:
                            prior_reflection_str = prior_reflection[2]
                        else:
                            prior_reflection_str = 'No prior reflections'
                        memories_str = str(memories['Content']) if memories is not None else 'No prior memories'

                        new_reflection = BhrLgcGPTProcess.generate_reflection_new(prior_reflection_str, memories_str, inputInHumanString, npcId)
                        logger.info("New Reflection: " + new_reflection)

                        BhrDBReflection.insert_into_table(db_conn, npcId, curTime, new_reflection)
                        # Reset the importance tracer
                        BhrDBReflectionTracer.insert_into_table(db_conn, npcId, 0, curTime, curTime)

            BhrDBJavaBuffer.mark_entry_as_fullyprocessed(db_conn, request_id)

            return 1

    except Exception as e:
        # Setup a generic logger if request_id is not available
        if logger:
            logger.error("An exception occurred:", exc_info=True)
        else:
            # If input_from_java is not defined or logger not set up
            logging.basicConfig(
                level=logging.ERROR,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(os.path.join(base_dir, 'BhrCtrl', 'error.log'), encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            logging.error("An exception occurred:", exc_info=True)
        return 0

    finally:
        if 'db_conn' in locals() and db_conn:
            db_conn.close()
            if logger:
                logger.info("Database connection closed.")