import sys
import os


# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

import DBConnect.DBCon as DBCon

from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule

import BhrLgcGPTProcess as BhrLgcGPTProcess
import BhrLgcInstToMemStre as BhrLgcInstToMemStre
import BhrLgcInputToMemStre as BhrLgcInputToMemStre
import BhrCtrl.BhrLgcProcessOnce as BhrLgcProcessOnce

import pandas as pd
import numpy as np
import json
import re
import pickle
import time

#Check DB exsist:

instruction_db_conn = schedule_db_conn = buffer_db_conn = reflection_tracer_db_conn = reflection_db_conne = memstre_db_conn = buffer_db_conn= DBCon.establish_sql_connection()
if not BhrDBJavaBuffer.database_exists(buffer_db_conn):
    BhrDBJavaBuffer.create_database(buffer_db_conn)

if not BhrDBJavaBuffer.table_exists(buffer_db_conn):
    BhrDBJavaBuffer.create_table(buffer_db_conn)
if not BhrDBMemStre.table_exists(memstre_db_conn):
    BhrDBMemStre.create_table(memstre_db_conn)
if not BhrDBReflection.table_exists(reflection_db_conne):
    BhrDBReflection.create_table(reflection_db_conne)
if not BhrDBReflectionTracer.table_exists(reflection_tracer_db_conn):
    BhrDBReflectionTracer.create_table(reflection_tracer_db_conn)
if not BhrDBSchedule.table_exists(schedule_db_conn):
    BhrDBSchedule.create_table(schedule_db_conn)
if not BhrDBInstruction.instruction_table_exists(instruction_db_conn):
    BhrDBInstruction.create_instruction_table(instruction_db_conn)

    
BhrDBJavaBuffer.delete_all_content_in_buffer(buffer_db_conn)
BhrDBInstruction.delete_all_instructions(instruction_db_conn)
BhrDBSchedule.delete_all_content(schedule_db_conn)
BhrDBReflectionTracer.delete_all_entries(reflection_tracer_db_conn)
BhrDBReflection.delete_all_content(reflection_db_conne)
BhrDBMemStre.delete_all_content_in_buffer(memstre_db_conn)




n = 0
while True:
    print(f"Processing step {n}")
    BhrLgcProcessOnce.processOneInputGiveOneInstruction()
    time.sleep(0.1)
    n += 1