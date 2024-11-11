import mysql.connector
from mysql.connector import Error

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

def create_announce_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")  # Use the AITown database
        create_table_query = """
        CREATE TABLE IF NOT EXISTS announcement_announce_buffer (
            npcId INT NOT NULL,
            theme LONGTEXT,
            `order` INT NOT NULL,
            content LONGTEXT,
            time DATETIME NOT NULL,
            isSent BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (npcId, `order`)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'announcement_announce_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def insert_into_announce_table(connection, npcId, theme, order, content, time, isSent=False):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown") 
        insert_query = """
        INSERT INTO announcement_announce_buffer (npcId, theme, `order`, content, time, isSent)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE content = VALUES(content), time = VALUES(time), isSent = VALUES(isSent)
        """
        cursor.execute(insert_query, (npcId, theme, order, content, time, isSent))
        connection.commit()
        print(f"Announcement inserted successfully: npcId={npcId}, theme={theme}, order={order}, content length={len(content)}, time={time}, isSent={isSent}")
    except Error as e:
        print(f"Failed to insert announcement: {e}")

def delete_all_announcements(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        delete_query = "DELETE FROM announcement_announce_buffer"
        cursor.execute(delete_query)
        connection.commit()
        print("All announcements in the 'announcement_announce_buffer' table have been deleted successfully.")
    except Error as e:
        print(f"Failed to delete announcements: {e}")

def get_earliest_order_announcement(connection, npcId):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        query = """
        SELECT * FROM announcement_announce_buffer 
        WHERE npcId = %s AND isSent = FALSE
        ORDER BY `order` ASC 
        LIMIT 1
        """
        cursor.execute(query, (npcId,))
        result = cursor.fetchone()
        if result:
            print(f"Earliest announcement for npcId={npcId}: theme={result[1]}, order={result[2]}, content={result[3]}, time={result[4]}")
            return result
        else:
            print(f"No unsent announcements found for npcId={npcId}.")
            return None
    except Error as e:
        print(f"Failed to retrieve earliest order announcement: {e}")
        return None

def mark_announcement_as_sent(connection, npcId, order):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        update_query = """
        UPDATE announcement_announce_buffer
        SET isSent = TRUE
        WHERE npcId = %s AND `order` = %s
        """
        cursor.execute(update_query, (npcId, order))
        connection.commit()
        print(f"Announcement with npcId={npcId} and order={order} marked as sent.")
    except Error as e:
        print(f"Failed to mark announcement as sent: {e}")

def create_database(connection):
    db_name = 'AITown'
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' checked/created successfully.")
    except Error as e:
        print(f"Failed to create database '{db_name}': {e}")

def table_exists(connection, table_name = 'announcement_announce_buffer'):
    db_name = 'AITown'
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = %s
        """, (table_name,))
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

def create_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")  # Use the AITown database
        create_table_query = """
        CREATE TABLE IF NOT EXISTS announcement_announce_buffer (
            npcId INT NOT NULL,
            theme LONGTEXT,
            `order` INT NOT NULL,
            content LONGTEXT,
            time DATETIME NOT NULL,
            isSent BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (npcId, `order`)
        )
        """
        cursor.execute(create_table_query)
        print("Table 'announcement_announce_buffer' checked/created successfully.")
    except Error as e:
        print(f"Failed to create table: {e}")

def get_latest_n_announcements(connection, npcId, n):
    try:
        cursor = connection.cursor()
        cursor.execute("USE AITown")
        query = """
        SELECT theme, `order`, content, time, isSent FROM announcement_announce_buffer 
        WHERE npcId = %s
        ORDER BY `order` DESC 
        LIMIT %s
        """
        cursor.execute(query, (npcId, n))
        results = cursor.fetchall()
        if results:
            print(f"Latest {n} announcements for npcId={npcId}:")
            for result in results:
                print(f"theme={result[0]}, order={result[1]}, content={result[2]}, time={result[3]}, isSent={result[4]}")
            return results
        else:
            print(f"No announcements found for npcId={npcId}.")
            return []
    except Error as e:
        print(f"Failed to retrieve latest {n} announcements: {e}")
        return []