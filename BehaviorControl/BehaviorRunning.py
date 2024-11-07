import sys
import os
sys.path.append('../DBmanipulation')

import DBCon
import BehaviorJavaBufferDB
import BehaviorReflectionTracerDB
import BehaviorMemStreDB
import BehaviorReflectionDB
import BehaviorScheduleDB

import BehaviorGPTProcess
import BehaviorInstToMemStre
import BehaviorInputToMemStre
import BehaviorInstructionDB
import BehaviorProcessOnece

import pandas as pd
import numpy as np
import json
import re
import pickle
import time

#Check DB exsist:

instruction_db_conn = schedule_db_conn = buffer_db_conn = reflection_tracer_db_conn = reflection_db_conne = memstre_db_conn = buffer_db_conn= DBCon.establish_sql_connection()
if not BehaviorJavaBufferDB.database_exists(buffer_db_conn):
    BehaviorJavaBufferDB.create_database(buffer_db_conn)

if not BehaviorJavaBufferDB.table_exists(buffer_db_conn):
    BehaviorJavaBufferDB.create_table(buffer_db_conn)
if not BehaviorMemStreDB.table_exists(memstre_db_conn):
    BehaviorMemStreDB.create_table(memstre_db_conn)
if not BehaviorReflectionDB.table_exists(reflection_db_conne):
    BehaviorReflectionDB.create_table(reflection_db_conne)
if not BehaviorReflectionTracerDB.table_exists(reflection_tracer_db_conn):
    BehaviorReflectionTracerDB.create_table(reflection_tracer_db_conn)
if not BehaviorScheduleDB.table_exists(schedule_db_conn):
    BehaviorScheduleDB.create_table(schedule_db_conn)
if not BehaviorInstructionDB.instruction_table_exists(instruction_db_conn):
    BehaviorInstructionDB.create_instruction_table(instruction_db_conn)

    
BehaviorJavaBufferDB.delete_all_content_in_buffer(buffer_db_conn)
BehaviorInstructionDB.delete_all_instructions(instruction_db_conn)
BehaviorScheduleDB.delete_all_content(schedule_db_conn)
BehaviorReflectionTracerDB.delete_all_entries(reflection_tracer_db_conn)
BehaviorReflectionDB.delete_all_content(reflection_db_conne)
BehaviorMemStreDB.delete_all_content_in_buffer(memstre_db_conn)




n = 0
while True:
    print(f"Processing step {n}")
    BehaviorProcessOnece.processOneInputGiveOneInstruction()
    time.sleep(1)
    n += 1