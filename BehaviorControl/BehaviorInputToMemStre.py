import sys
import os

# Add the DBmanipulation folder to the Python path
sys.path.append('../DBmanipulation')

# Now import the required functions from BufferDB

import DBCon
import BehaviorMemStreDB
import BehaviorReflectionTracerDB

import json
import re

import pickle

import BehaviorGPTProcess


def inputToMemStre(java_input):
    # Establish a connection to the database
    row_dict_str = java_input[2]
    row_dict = json.loads(row_dict_str)
    memstre_db_connection =   DBCon.establish_sql_connection()
    print(type(row_dict['npc']['talk']['isTalking']))
    print(row_dict['npc']['talk']['isTalking'])
    if row_dict['npc']['talk']['isTalking'] == True:
        print('conversation received')
        MemString = BehaviorGPTProcess.javaConvInputtoHumanString(row_dict['npc']['talk'])
        insert_npcId = java_input[1]
        insert_time = java_input[0]
        insert_content = MemString
        insert_importance = BehaviorGPTProcess.get_importance(MemString)
        insert_embedding= BehaviorGPTProcess.get_embedding(MemString)
        insert_isInstruction = 0
        BehaviorMemStreDB.insert_into_table(memstre_db_connection, insert_npcId, insert_time, insert_isInstruction,insert_content, insert_importance, insert_embedding)

    return 0


# Need to See other people's actiona as well.
def inputImportancetoReflectionTracer(java_input):
    row_dict_string = java_input[2]
    ReflectionTracer_db_conection =   DBCon.establish_sql_connection()
    if not BehaviorReflectionTracerDB.table_exists(ReflectionTracer_db_conection):
        BehaviorReflectionTracerDB.create_table(ReflectionTracer_db_conection)
    row_dict = json.loads(row_dict_string)
    if row_dict['npc']['talk']['isTalking'] == 'true':
        MemString = parse_npc_info(row_dict['npc']['talk'])
        insert_npcId = row_dict['npc']['npcId']
        insert_time = row_dict['time']
        insert_importance = int(get_importance(MemString))
        output = BehaviorReflectionTracerDB.retrieve_entry(ReflectionTracer_db_conection, insert_npcId)
        if output == None:
            BehaviorReflectionTracerDB.insert_into_table(ReflectionTracer_db_conection, insert_npcId, insert_importance, insert_time, insert_time)
            return 0
        total_importance, start_time, end_time  = output[0], output[1], output[2]
        BehaviorReflectionTracerDB.insert_into_table(ReflectionTracer_db_conection, insert_npcId, total_importance + insert_importance, start_time,insert_time)

    return 0