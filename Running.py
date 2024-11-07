import sys
import os
sys.path.append('./DBmanipulation')
sys.path.append('./AIMemory')

import DBCon
import BufferDB
import ReflectionTracerDB
import MemStreDB
import ReflectionDB
import ScheduleDB
import GPTProcess
import InstToMemStre
import InputToMemStre
import InstructionDB

import pandas as pd
import numpy as np
import json
import re
import pickle
import time

#Check DB exsist:

instruction_db_conn = schedule_db_conn = buffer_db_conn = reflection_tracer_db_conn = reflection_db_conne = memstre_db_conn = buffer_db_conn= DBCon.establish_sql_connection()
if not BufferDB.database_exists(buffer_db_conn):
    BufferDB.create_database(buffer_db_conn)

if not BufferDB.table_exists(buffer_db_conn):
    BufferDB.create_table(buffer_db_conn)
if not MemStreDB.table_exists(memstre_db_conn):
    MemStreDB.create_table(memstre_db_conn)
if not ReflectionDB.table_exists(reflection_db_conne):
    ReflectionDB.create_table(reflection_db_conne)
if not ReflectionTracerDB.table_exists(reflection_tracer_db_conn):
    ReflectionTracerDB.create_table(reflection_tracer_db_conn)
if not ScheduleDB.table_exists(schedule_db_conn):
    ScheduleDB.create_table(schedule_db_conn)
if not InstructionDB.instruction_table_exists(instruction_db_conn):
    InstructionDB.create_instruction_table(instruction_db_conn)

    
BufferDB.delete_all_content_in_buffer(buffer_db_conn)
InstructionDB.delete_all_instructions(instruction_db_conn)
ScheduleDB.delete_all_content(schedule_db_conn)
ReflectionTracerDB.delete_all_entries(reflection_tracer_db_conn)
ReflectionDB.delete_all_content(reflection_db_conne)
MemStreDB.delete_all_content_in_buffer(memstre_db_conn)


import ProcessOnece

n = 0
while True:
    print(f"Processing step {n}")
    ProcessOnece.processOneInputGiveOneInstruction()
    time.sleep(1)
    n += 1
