

import mysql.connector
from mysql.connector import Error
import configparser
import os

def establish_sql_connection():
    # Print the current working directory for debugging
    print("Current working directory:", os.getcwd())
    
    config = configparser.ConfigParser()
    # Adjust path to look for config.ini in AImodule regardless of the current directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config.ini')
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
            print("Connected to MySQL server and database 'AITown'")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None