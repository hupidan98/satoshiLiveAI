import mysql.connector
from mysql.connector import Error
import pickle  # To serialize and deserialize Python objects (like the embedding list)
import pandas as pd

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

def create_database(connection, db_name):
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
        CREATE TABLE IF NOT EXISTS memeory_stream (
            npcID VARCHAR(255) NOT NULL,
            Time DATETIME NOT NULL,
            isInstruction BOOLEAN DEFAULT FALSE,
            Content LONGTEXT,
            Importance INT CHECK (Importance BETWEEN 1 AND 10),
            Embedding BLOB,
            PRIMARY KEY (npcID, Time, isInstruction)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'memeory_stream' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def delete_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_table_query = "DROP TABLE IF EXISTS memeory_stream"
        cursor.execute(delete_table_query)
        connection.commit()
        print("Table 'memeory_stream' has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete table 'memeory_stream': {e}")

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'memeory_stream'
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

def insert_into_table(connection, npcID, time, isInstruction, content, importance, embedding):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        # Serialize the embedding list
        embedding_blob = pickle.dumps(embedding)
        insert_query = """
        INSERT INTO memeory_stream (npcID, Time, isInstruction, Content, Importance, Embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE Content = VALUES(Content), Importance = VALUES(Importance), Embedding = VALUES(Embedding)
        """
        cursor.execute(insert_query, (npcID, time, isInstruction, content, importance, embedding_blob))
        connection.commit()
        print(f"Data inserted successfully: npcID={npcID}, time={time}, isInstruction={isInstruction}, content length={len(content)}, importance={importance}")
    except Error as e:
        print(f"Failed to insert data: {e}")

def retrieve_entry(connection, npcID, time, isInstruction):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        select_query = "SELECT Content, Importance, Embedding FROM memeory_stream WHERE npcID = %s AND Time = %s AND isInstruction = %s"
        cursor.execute(select_query, (npcID, time, isInstruction))
        result = cursor.fetchone()
        if result:
            content, importance, embedding_blob = result
            # Deserialize the embedding back to a list
            embedding = pickle.loads(embedding_blob)
            print(f"Retrieved entry: content={content}, importance={importance}, embedding length={len(embedding)}")
            return content, importance, embedding
        else:
            print(f"No entry found for npcID={npcID}, time={time}, isInstruction={isInstruction}")
            return None
    except Error as e:
        print(f"Failed to retrieve data: {e}")
        return None

def delete_entry_in_buffer(connection, npcID, time, isInstruction):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_query = "DELETE FROM memeory_stream WHERE npcID = %s AND Time = %s AND isInstruction = %s"
        cursor.execute(delete_query, (npcID, time, isInstruction))
        connection.commit()
        print(f"Entry with npcID={npcID}, time={time}, isInstruction={isInstruction} has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete entry: {e}")

def delete_all_content_in_buffer(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_query = "DELETE FROM memeory_stream"
        cursor.execute(delete_query)
        connection.commit()
        print("All content in the 'memeory_stream' table has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete content: {e}")


def retrieve_most_recent_entries(connection, npcID, before_time, limit=300):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        select_query = """
        SELECT npcID, Time, isInstruction, Content, Importance, Embedding
        FROM memeory_stream
        WHERE npcID = %s AND Time < %s
        ORDER BY Time DESC
        LIMIT %s
        """
        cursor.execute(select_query, (npcID, before_time, limit))
        results = cursor.fetchall()

        # Prepare data for DataFrame
        data = []
        for result in results:
            npcID, time, isInstruction, content, importance, embedding_blob = result
            # Deserialize the embedding back to a list
            embedding = pickle.loads(embedding_blob)
            data.append([npcID, time, isInstruction, content, importance, embedding])

        # Define DataFrame columns
        columns = ['npcID', 'Time', 'isInstruction', 'Content', 'Importance', 'Embedding']

        # Create DataFrame
        df = pd.DataFrame(data, columns=columns)
        
        print(f"Retrieved {len(df)} entries for npcID={npcID} before time={before_time}")
        return df
    except Error as e:
        print(f"Failed to retrieve data: {e}")
        return None


def retrieve_entries_between_time(connection, npcID, start_time, end_time, limit=300):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        select_query = """
        SELECT npcID, Time, isInstruction, Content, Importance, Embedding
        FROM memeory_stream
        WHERE npcID = %s AND Time BETWEEN %s AND %s
        ORDER BY Time ASC
        LIMIT %s
        """
        cursor.execute(select_query, (npcID, start_time, end_time, limit))
        results = cursor.fetchall()

        # Prepare data for DataFrame
        data = []
        for result in results:
            npcID, time, isInstruction, content, importance, embedding_blob = result
            # Deserialize the embedding back to a list
            embedding = pickle.loads(embedding_blob)
            data.append([npcID, time, isInstruction, content, importance, embedding])

        # Define DataFrame columns
        columns = ['npcID', 'Time', 'isInstruction', 'Content', 'Importance', 'Embedding']

        # Create DataFrame
        df = pd.DataFrame(data, columns=columns)
        
        print(f"Retrieved {len(df)} entries for npcID={npcID} between {start_time} and {end_time}")
        return df
    except Error as e:
        print(f"Failed to retrieve data: {e}")
        return None
