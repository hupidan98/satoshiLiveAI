import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor


# Import project-specific modules
import DBConnect.DBCon as DBCon
from DBConnect import BhrDBJavaBuffer
from DBConnect import BhrDBInstruction
from DBConnect import BhrDBReflectionTracer
from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection
from DBConnect import BhrDBSchedule
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

# Add the base directory (one level up)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

# Initialize the database
global_db_conn = DBCon.establish_sql_connection()

# Create or validate tables
def initialize_database(db_conn):
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

# Call the database initialization function
initialize_database(global_db_conn)

# Define the function to process tasks with safe connection handling
def process_task(task_id):
    db_conn = None
    try:
        print(f"Processing task {task_id}")
        BhrLgcProcessOnce.processOneInputGiveOneInstruction()
        print(f"Task {task_id} completed.")
    except Exception as e:
        print(f"Error processing task {task_id}: {e}")
    finally:
        if db_conn:
            print(f"Closing connection for task {task_id}")
            db_conn.close()

# Main loop to run tasks in parallel
n = 0
num_workers = 4  # Number of parallel tasks
try:
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        while True:
            futures = [executor.submit(process_task, n + i) for i in range(num_workers)]
            for future in futures:
                future.result()  # Wait for each task to complete
            n += num_workers
            time.sleep(2)  # Adjust sleep interval to control task submission rate
except KeyboardInterrupt:
    print("Loop terminated by user.")
finally:
    # Close the global database connection and reset stdout/stderr
    global_db_conn.close()
    sys.stdout.log.close()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__