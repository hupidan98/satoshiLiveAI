import mysql.connector
from mysql.connector import Error
import configparser
import os

def check_connection(connection):
    if connection.is_connected():
        print("Connection is still active.")
    else:
        print("Connection is not active. Reconnecting...")
        connection.reconnect(attempts=3, delay=5)
        if connection.is_connected():
            print("Reconnection successful.")
        else:
            print("Reconnection failed.")

def create_database(connection):
    db_name = 'AITown'
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' checked/created successfully.")
    except Error as e:
        print(f"Failed to create database '{db_name}': {e}")

def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS commentreply_java_buffer (
            requestId INT AUTO_INCREMENT,
            time DATETIME NOT NULL,
            npcId INT NOT NULL,
            msgId INT NOT NULL,
            senderId INT NOT NULL,
            content LONGTEXT,
            isProcessed BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (requestId)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'commentreply_java_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def insert_into_table(connection, time, npcId, msgId, senderId, content, isProcessed=False):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown") 
        insert_query = """
        INSERT INTO commentreply_java_buffer (time, npcId, msgId, senderId, content, isProcessed)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE content = VALUES(content), isProcessed = VALUES(isProcessed)
        """
        cursor.execute(insert_query, (time, npcId, msgId, senderId, content, isProcessed))
        connection.commit()
        print(f"Data inserted successfully: time={time}, npcId={npcId}, msgId={msgId}, senderId={senderId}, content length={len(content)}, isProcessed={isProcessed}")
    except Error as e:
        print(f"Failed to insert data: {e}")

def get_earliest_unprocessed_entry(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        query = """
        SELECT * FROM commentreply_java_buffer 
        WHERE isProcessed = FALSE
        ORDER BY time ASC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"Earliest unprocessed entry: requestId={result[0]}, time={result[1]}, npcId={result[2]}, msgId={result[3]}, senderId={result[4]}, content={result[5]}")
            return result
        else:
            print("No unprocessed entries found.")
            return None
    except Error as e:
        print(f"Failed to retrieve earliest unprocessed entry: {e}")
        return None

def mark_entry_as_processed(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        update_query = """
        UPDATE commentreply_java_buffer
        SET isProcessed = TRUE
        WHERE requestId = %s
        """
        cursor.execute(update_query, (requestId,))
        connection.commit()
        print(f"Entry with requestId={requestId} marked as processed.")
    except Error as e:
        print(f"Failed to mark entry as processed: {e}")

def delete_entry_in_buffer(connection, requestId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_query = "DELETE FROM commentreply_java_buffer WHERE requestId = %s"
        cursor.execute(delete_query, (requestId,))
        connection.commit()
        print(f"Entry with requestId={requestId} has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete entry: {e}")

# Other functions like `get_unprocessed_entries_of_npc`, `get_all_unprocessed_entries`, `delete_all_content_in_buffer` can be similarly updated.