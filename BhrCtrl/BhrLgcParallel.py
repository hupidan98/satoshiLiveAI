import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor
import logging
from logging.handlers import RotatingFileHandler

# Add the base directory (one level up from the current directory)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)

# Import project-specific modules
from DBConnect import DBCon
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

# Initialize the database
global_db_conn = DBCon.establish_sql_connection()

# Create or validate tables
def initialize_database(db_conn):
    BhrDBJavaBuffer.delete_database(db_conn, 'AITown')

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

# Setup a global logger with RotatingFileHandler
logger = logging.getLogger("ParallelLogger")
logger.setLevel(logging.INFO)

# Define log file path
log_file_path = os.path.join(base_dir, 'BhrCtrl', 'parallel.log')

# Create RotatingFileHandler: 5MB per file, keep 5 backups
handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to the logger
if not logger.handlers:
    logger.addHandler(handler)

# Also add StreamHandler to output logs to stdout
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Define the function to process tasks with safe connection handling
def process_task(task_id):
    try:
        logger.info(f"Processing task {task_id}")
        BhrLgcProcessOnce.processOneInputGiveOneInstruction()
        logger.info(f"Task {task_id} completed.")
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}", exc_info=True)

# Main loop to run tasks in parallel
n = 0
num_workers = 15  # Number of parallel tasks
try:
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        while True:
            futures = [executor.submit(process_task, n + i) for i in range(num_workers)]
            for future in futures:
                future.result()  # Wait for each task to complete
            n += num_workers
            time.sleep(2)  # Adjust sleep interval to control task submission rate
except KeyboardInterrupt:
    logger.info("Loop terminated by user.")
except Exception as e:
    logger.error("An unexpected error occurred in the main loop.", exc_info=True)
finally:
    # Close the global database connection
    if global_db_conn:
        global_db_conn.close()
        logger.info("Global database connection closed.")