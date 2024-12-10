import sys
import os
import time
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
import BhrCtrl.BhrLgcProcessOnce as BhrLgcProcessOnce

# Establish a database connection
db_conn = DBCon.establish_sql_connection()

# Initialize the database by creating required tables
def initialize_database(db_conn):
    print("Initializing database...")
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

# Call the initialization function
initialize_database(db_conn)

# Infinite loop to process tasks
n = 0
try:
    while True:
        print(f"Processing step {n}")
        # Call the core processing function
        BhrLgcProcessOnce.processOneInputGiveOneInstruction()
        print("\n" * 5)  # Add spacing between iterations for clarity
        time.sleep(2)  # Adjust the sleep interval as needed
        n += 1
except KeyboardInterrupt:
    print("Loop terminated by user.")