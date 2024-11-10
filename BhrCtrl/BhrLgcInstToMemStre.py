import sys
import os

# Add the DBmanipulation folder to the Python path

import DBConnect.DBCon as DBCon

from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflectionTracer

import json
import re

import pickle

import BhrLgcGPTProcess
import BhrLgcManualProcess

memstre_db_connection = DBCon.establish_sql_connection()

def InstToMemStreDB(input_from_java, instruction):

    output_str = BhrLgcGPTProcess.InstructionToHumanString(instruction)
    insert_npcId = input_from_java[1]
    insert_time = input_from_java[0]
    
    insert_content = output_str
    insert_importance = BhrLgcGPTProcess.get_importance(output_str)
    insert_embedding= BhrLgcGPTProcess.get_embedding(output_str)
    insert_isInstruction = 1

    BehaviorDBMemStre.insert_into_table(memstre_db_connection, insert_npcId, insert_time, insert_isInstruction,insert_content, insert_importance, insert_embedding)
    return 0

def InstToMemStreSatoshiDB(input_from_java, words):

    insert_npcId = input_from_java[1]
    insert_time = input_from_java[0]
    
    insert_content = words
    insert_importance = BhrLgcGPTProcess.get_importance(words)
    insert_embedding= BhrLgcGPTProcess.get_embedding(words)
    insert_isInstruction = 1

    BhrDBMemStre.insert_into_table(memstre_db_connection, insert_npcId, insert_time, insert_isInstruction,insert_content, insert_importance, insert_embedding)
    return 0


# Need to See other people's actiona as well.
# def InstImportancetoReflectionTracer(input_from_java, instruction):
#     ReflectionTracer_db_conection =   DBCon.establish_sql_connection()
#     if not ReflectionTracerDB.table_exists(ReflectionTracer_db_conection):
#         ReflectionTracerDB.create_table(ReflectionTracer_db_conection)

#     output_str = GPTProcess.parse_npc_info(instruction)
#     input_from_java_string = input_from_java[2]
#     inputdict = json.loads(input_from_java_string)
#     print(input_from_java)
#     insert_npcId = input_from_java[1]
#     insert_time = input_from_java[0]

#     insert_importance = int(GPTProcess.get_importance(output_str))
    
#     output = ReflectionTracerDB.retrieve_entry(ReflectionTracer_db_conection, insert_npcId)

#     print(insert_npcId, insert_importance, insert_time)
#     if output == None:

#         ReflectionTracerDB.insert_into_table(ReflectionTracer_db_conection, insert_npcId, insert_importance, insert_time, insert_time)
#         return 0
#     total_importance, start_time, end_time  = output[0], output[1], output[2]
#     ReflectionTracerDB.insert_into_table(ReflectionTracer_db_conection, insert_npcId, total_importance + insert_importance, start_time,insert_time)

#     return 0


def InstImportancetoReflectionTracer(input_from_java, instruction, words_to_say):
    ReflectionTracer_db_conection =   DBCon.establish_sql_connection()
    if not BhrDBReflectionTracer.table_exists(ReflectionTracer_db_conection):
        BhrDBReflectionTracer.create_table(ReflectionTracer_db_conection)

    # output_str = GPTProcess.parse_npc_info(instruction)
    
    input_from_java_string = input_from_java[2]
    
    # instruction = instruction.replace('\n', '\\n')
    # instruction = instruction.replace('\t', '\\t')
    # print(instruction)
    # inputdict = json.loads(instruction)
    output_str = 'Satoshi says' + words_to_say
    insert_npcId = input_from_java[1]
    insert_time = input_from_java[0]

    insert_importance = int(BhrLgcGPTProcess.get_importance(output_str))
    
    output = BhrDBReflectionTracer.retrieve_entry(ReflectionTracer_db_conection, insert_npcId)

    print(insert_npcId, insert_importance, insert_time)
    if output == None:

        BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, insert_importance, insert_time, insert_time)
        return 0
    total_importance, start_time, end_time  = output[0], output[1], output[2]
    BhrDBReflectionTracer.insert_into_table(ReflectionTracer_db_conection, insert_npcId, total_importance + insert_importance, start_time,insert_time)

    return 0