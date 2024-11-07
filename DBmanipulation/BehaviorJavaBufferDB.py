import mysql.connector
from mysql.connector import Error

import configparser
import os





    
def check_connection(connection):
    if connection.is_connected():
        print("Connection is still active.")
    else:
        print("Connection is not active. Reconnecting...")
        connection.reconnect(attempts=3, delay=5)  # Attempt to reconnect 3 times with a 5-second delay
        if connection.is_connected():
            print("Reconnection successful.")
        else:
            print("Reconnection failed.")

def delete_database(connection, db_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        print(f"Database '{db_name}' deleted successfully.")
    except Error as e:
        print(f"Failed to delete database '{db_name}': {e}")

def list_databases(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("Remaining databases:")
        for db in databases:
            print(db[0])
    except Error as e:
        print(f"Failed to list databases: {e}")

def create_database(connection):
    db_name = 'AITown'
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' checked/created successfully.")
    except Error as e:
        print(f"Failed to create database '{db_name}': {e}")

def database_exists(connection):
    db_name = 'AITown'
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
        result = cursor.fetchone()
        if result:
            print(f"Database '{db_name}' exists.")
            return True
        else:
            print(f"Database '{db_name}' does not exist.")
            return False
    except Error as e:
        print(f"Failed to check if database exists: {e}")
        return False
    
def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")  # Use the AITown database
        create_table_query = """
        CREATE TABLE IF NOT EXISTS behavior_java_buffer (
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            content LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (time, npcId)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'behavior_java_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def delete_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")  # Ensure you're using the correct database
        delete_table_query = f"DROP TABLE IF EXISTS behavior_java_buffer"
        cursor.execute(delete_table_query)
        connection.commit()
        print(f"Table behavior_java_buffer has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete table behavior_java_buffer: {e}")

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'behavior_java_buffer'
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = '{table_name}'
        """)
        result = cursor.fetchone()
        if result:
            print(f"Table '{table_name}' exists in database '{db_name}'.")
            return True
        else:
            print(f"Table '{table_name}' does not exist in database '{db_name}'.")
            return False
    except Error as e:
        print(f"Failed to check if table exists: {e}")
        return False

def insert_into_table(connection, time, npcId, content, isProcessed=False):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown") 
        insert_query = """
        INSERT INTO behavior_java_buffer (time, npcId, content, isProcessed)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE content = VALUES(content), isProcessed = VALUES(isProcessed)
        """
        cursor.execute(insert_query, (time, npcId, content, isProcessed))
        connection.commit()
        print(f"Data inserted successfully: time={time}, npcId={npcId}, content length={len(content)}, isProcessed={isProcessed}")
    except Error as e:
        print(f"Failed to insert data: {e}")

def delete_entry_in_buffer(connection, time, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")  # Ensure you're using the correct database
        delete_query = "DELETE FROM behavior_java_buffer WHERE time = %s AND npcId = %s"
        cursor.execute(delete_query, (time, npcId))
        connection.commit()  # Commit the changes
        print(f"Entry with time={time} and npcId={npcId} has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete entry: {e}")

def delete_all_content_in_buffer(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")  # Ensure you're using the correct database
        delete_query = "DELETE FROM behavior_java_buffer"
        cursor.execute(delete_query)
        connection.commit()  # Commit the changes
        print("All content in the 'behavior_java_buffer' table has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete content: {e}")

# Function 1: Get the earliest unprocessed entry
def get_earliest_unprocessed_entry(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        query = """
        SELECT * FROM behavior_java_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"Earliest unprocessed entry: time={result[0]}, npcId={result[1]}, content={result[2]}")
            return result
        else:
            print("No unprocessed entries found.")
            return None
    except Error as e:
        print(f"Failed to retrieve earliest unprocessed entry: {e}")
        return None
    

def get_unprocessed_entries_of_npc(connection, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        
        # Query for all unprocessed entries for the given npcId
        query_all = """
        SELECT * FROM behavior_java_buffer 
        WHERE isProcessed = FALSE AND npcId = %s
        ORDER BY time ASC
        """
        cursor.execute(query_all, (npcId,))
        all_unprocessed_of_a_npc = cursor.fetchall()
        
        # Query for the latest unprocessed entry for the given npcId
        query_latest = """
        SELECT * FROM behavior_java_buffer 
        WHERE isProcessed = FALSE AND npcId = %s
        ORDER BY time DESC 
        LIMIT 1
        """
        cursor.execute(query_latest, (npcId,))
        latest_unprocessed_of_a_npc = cursor.fetchone()
        
        if all_unprocessed_of_a_npc:
            print(f"Found {len(all_unprocessed_of_a_npc)} unprocessed entries for npcId={npcId}.")
        else:
            print(f"No unprocessed entries found for npcId={npcId}.")
        
        if latest_unprocessed_of_a_npc:
            print(f"Latest unprocessed entry for npcId={npcId}: time={latest_unprocessed_of_a_npc[0]}")
        else:
            print(f"No latest unprocessed entry found for npcId={npcId}.")

        return all_unprocessed_of_a_npc, latest_unprocessed_of_a_npc
    
    except Error as e:
        print(f"Failed to retrieve unprocessed entries for npcId={npcId}: {e}")
        return [], None


# Function 2: Mark an entry as processed
def mark_entry_as_processed(connection, time, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        update_query = """
        UPDATE behavior_java_buffer
        SET isProcessed = TRUE
        WHERE time = %s AND npcId = %s
        """
        cursor.execute(update_query, (time, npcId))
        connection.commit()
        print(f"Entry with time={time} and npcId={npcId} marked as processed.")
    except Error as e:
        print(f"Failed to mark entry as processed: {e}")

# Function 3: Get all unprocessed entries
def get_all_unprocessed_entries(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        query = """
        SELECT * FROM behavior_java_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            print("Unprocessed entries:")
            for result in results:
                print(f"time={result[0]}, npcId={result[1]}, content length={len(result[2])}")
            return results
        else:
            print("No unprocessed entries found.")
            return []
    except Error as e:
        print(f"Failed to retrieve unprocessed entries: {e}")
        return []


def mark_entry_as_processed(connection, time, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        update_query = """
        UPDATE behavior_java_buffer
        SET isProcessed = TRUE
        WHERE time = %s AND npcId = %s
        """
        cursor.execute(update_query, (time, npcId))
        connection.commit()
        print(f"Entry with time={time} and npcId={npcId} marked as processed.")
    except Error as e:
        print(f"Failed to mark entry as processed: {e}")