import mysql.connector
from mysql.connector import Error
import configparser
import os

def establish_sql_connection():
    # Print the current working directory for debugging
    print("Current working directory:", os.getcwd())
    
    config = configparser.ConfigParser()
    # Use the path relative to this file's location to locate config.ini
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"Error: config.ini not found at {config_path}")
        return None
    
    config.read(config_path)
    
    print("Config sections found:", config.sections())
    
    if 'mysql' not in config:
        print("Error: 'mysql' section not found in config.ini")
        return None
    
    try:
        connection = mysql.connector.connect(
            host=config['mysql']['host'],
            user=config['mysql']['user'],
            password=config['mysql']['password']
        )
        if connection.is_connected():
            print("Connected to MySQL server successfully")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None