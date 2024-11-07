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
        CREATE TABLE IF NOT EXISTS reflection_tracer (
            npcID VARCHAR(255) NOT NULL,
            total_importance INT CHECK (total_importance >= 0),
            start_Time DATETIME NOT NULL,
            end_Time DATETIME NOT NULL,
            PRIMARY KEY (npcID)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'reflection_tracer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def delete_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_table_query = "DROP TABLE IF EXISTS reflection_tracer"
        cursor.execute(delete_table_query)
        connection.commit()
        print("Table 'reflection_tracer' has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete table 'reflection_tracer': {e}")

def table_exists(connection):
    db_name = 'AITown'
    table_name = 'reflection_tracer'
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

def insert_into_table(connection, npcID, total_importance, start_time, end_time):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        insert_query = """
        INSERT INTO reflection_tracer (npcID, total_importance, start_Time, end_Time)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE total_importance = VALUES(total_importance), start_Time = VALUES(start_Time), end_Time = VALUES(end_Time)
        """
        cursor.execute(insert_query, (npcID, total_importance, start_time, end_time))
        connection.commit()
        print(f"Data inserted successfully: npcID={npcID}, total_importance={total_importance}, start_time={start_time}, end_time={end_time}")
    except Error as e:
        print(f"Failed to insert data: {e}")

def retrieve_entry(connection, npcID):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        select_query = "SELECT total_importance, start_Time, end_Time FROM reflection_tracer WHERE npcID = %s"
        cursor.execute(select_query, (npcID,))
        result = cursor.fetchone()
        if result:
            total_importance, start_time, end_time = result
            print(f"Retrieved entry: npcID={npcID}, total_importance={total_importance}, start_time={start_time}, end_time={end_time}")
            return total_importance, start_time, end_time
        else:
            print(f"No entry found for npcID={npcID}")
            return None
    except Error as e:
        print(f"Failed to retrieve data: {e}")
        return None

def delete_entry_in_table(connection, npcID):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_query = "DELETE FROM reflection_tracer WHERE npcID = %s"
        cursor.execute(delete_query, (npcID,))
        connection.commit()
        print(f"Entry with npcID={npcID} has been deleted successfully.")
    except Error as e:
        print(f"Failed to delete entry: {e}")

def delete_all_entries(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_query = "DELETE FROM reflection_tracer"
        cursor.execute(delete_query)
        connection.commit()
        print("All entries in the 'reflection_tracer' table have been deleted successfully.")
    except Error as e:
        print(f"Failed to delete entries: {e}")
