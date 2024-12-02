# import sys
# import os


# # Add the base directory (one level up from AnnCtrl)
# base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.append(base_dir)

# import DBConnect.DBCon as DBCon

# from DBConnect import BhrDBJavaBuffer
# from DBConnect import BhrDBInstruction
# from DBConnect import BhrDBReflectionTracer
# from DBConnect import BhrDBMemStre
# from DBConnect import BhrDBReflection
# from DBConnect import BhrDBSchedule

# import BhrLgcGPTProcess as BhrLgcGPTProcess
# import BhrCtrl.BhrLgcToMemStre as BhrLgcToMemStre
# import BhrCtrl.BhrLgcProcessOnce as BhrLgcProcessOnce

# import pandas as pd
# import numpy as np
# import json
# import re
# import pickle
# import time

# #Check DB exsist:

# db_conn= DBCon.establish_sql_connection()
# BhrDBJavaBuffer.delete_database(db_conn, 'AITown')

# if not BhrDBJavaBuffer.database_exists(db_conn):
#     BhrDBJavaBuffer.create_database(db_conn)

# if not BhrDBJavaBuffer.table_exists(db_conn):
#     BhrDBJavaBuffer.create_table(db_conn)
# if not BhrDBMemStre.table_exists(db_conn):
#     BhrDBMemStre.create_table(db_conn)
# if not BhrDBReflection.table_exists(db_conn):
#     BhrDBReflection.create_table(db_conn)
# if not BhrDBReflectionTracer.table_exists(db_conn):
#     BhrDBReflectionTracer.create_table(db_conn)
# if not BhrDBSchedule.table_exists(db_conn):
#     BhrDBSchedule.create_table(db_conn)
# if not BhrDBInstruction.instruction_table_exists(db_conn):
#     BhrDBInstruction.create_instruction_table(db_conn)

    
# BhrDBJavaBuffer.delete_all_content_in_buffer(db_conn)
# BhrDBInstruction.delete_all_instructions(db_conn)
# BhrDBSchedule.delete_all_content(db_conn)
# BhrDBReflectionTracer.delete_all_entries(db_conn)
# BhrDBReflection.delete_all_content(db_conn)
# BhrDBMemStre.delete_all_content_in_buffer(db_conn)




# n = 0
# while True:
#     print(f"Processing step {n}")
#     BhrLgcProcessOnce.processOneInputGiveOneInstruction()
#     print()
#     print()
#     print()
#     print()
#     print()
#     time.sleep(2)
#     n += 1



import sys
import os
import time
import DBConnect.DBCon as DBCon
from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule
import BhrLgcGPTProcess as BhrLgcGPTProcess
import BhrCtrl.BhrLgcToMemStre as BhrLgcToMemStre
import BhrCtrl.BhrLgcProcessOnce as BhrLgcProcessOnce
import pandas as pd
import numpy as np
import json
import re
import pickle

# Define a Logger class for dual output
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)  # Write to console
        self.log.write(message)       # Write to file

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# Redirect output to both console and file
log_file_path = os.path.join(os.path.dirname(__file__), "output_log.txt")
sys.stdout = Logger(log_file_path)
sys.stderr = sys.stdout  # Capture any errors as well




# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

# Check DB exists
db_conn = DBCon.establish_sql_connection()
# BhrDBJavaBuffer.delete_database(db_conn, 'AITown')

if not BhrDBJavaBuffer.database_exists(db_conn):
    BhrDBJavaBuffer.create_database(db_conn)

if not BhrDBJavaBuffer.table_exists(db_conn):
    BhrDBJavaBuffer.create_table(db_conn)
if not BhrDBMemStre.table_exists(db_conn):
    BhrDBMemStre.create_table(db_conn)
if not BhrDBReflection.table_exists(db_conn):
    BhrDBReflection.create_table(db_conn)
if not BhrDBReflectionTracer.table_exists(db_conn):
    BhrDBReflectionTracer.create_table(db_conn)
if not BhrDBSchedule.table_exists(db_conn):
    BhrDBSchedule.create_table(db_conn)
if not BhrDBInstruction.instruction_table_exists(db_conn):
    BhrDBInstruction.create_instruction_table(db_conn)

# BhrDBJavaBuffer.delete_all_content_in_buffer(db_conn)
# BhrDBInstruction.delete_all_instructions(db_conn)
# BhrDBSchedule.delete_all_content(db_conn)
# BhrDBReflectionTracer.delete_all_entries(db_conn)
# BhrDBReflection.delete_all_content(db_conn)
# BhrDBMemStre.delete_all_content_in_buffer(db_conn)

# Run the infinite loop
n = 0
try:
    while True:
        print(f"Processing step {n}")
        BhrLgcProcessOnce.processOneInputGiveOneInstruction()
        print("\n" * 5)
        time.sleep(2)
        n += 1
except KeyboardInterrupt:
    print("Loop terminated by user.")
finally:
    # Reset stdout and stderr to default
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__