#!/usr/bin/env python3
"""
Script to insert ferry data from ferries.json into a MySQL database.
"""

import json
import os
import sys
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_json_data(file_path):
    """Load data from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error loading JSON from file {file_path}: {e}")
        return None

def create_connection():
    """Create a connection to the MySQL database"""
    try:
        # Get database connection details from environment variables
        db_host = os.getenv("MYSQL_HOST", "localhost")
        db_user = os.getenv("MYSQL_USER", "root")
        db_password = os.getenv("MYSQL_PASSWORD", "")
        db_name = os.getenv("MYSQL_DATABASE", "lighthouse")
        db_port = int(os.getenv("MYSQL_PORT", "3306"))
        
        # First connect without specifying a database
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=db_port
        )
        
        if connection.is_connected():
            print(f"Connected to MySQL server")
            
            # Create database if it doesn't exist
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.close()
            
            # Close the connection and reconnect with the database specified
            connection.close()
            
            connection = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                port=db_port
            )
            
            if connection.is_connected():
                print(f"Connected to MySQL database: {db_name}")
                return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
    
    return None

def create_ferries_table(connection):
    """Create the ferries table with all attributes from the JSON"""
    try:
        cursor = connection.cursor()
        
        # Create main ferries table
        create_ferries_table_query = """
        CREATE TABLE IF NOT EXISTS ferries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            pontos_vessel_id VARCHAR(100),
            length_over_all_m FLOAT,
            length_between_perpendiculars_m FLOAT,
            breadth_m FLOAT,
            draft_m FLOAT,
            max_speed_kn FLOAT,
            installed_power_kw FLOAT,
            capacity_passenger_car_equivalent INT,
            gross_tonnage FLOAT,
            net_tonnage FLOAT,
            number_of_engines INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_ferries_table_query)
        
        # Create engines table
        create_engines_table_query = """
        CREATE TABLE IF NOT EXISTS ferry_engines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ferry_id INT NOT NULL,
            type VARCHAR(100),
            power_kw FLOAT,
            rpm INT,
            location VARCHAR(50),
            year_manufactured INT,
            FOREIGN KEY (ferry_id) REFERENCES ferries(id) ON DELETE CASCADE
        )
        """
        cursor.execute(create_engines_table_query)
        
        # Create propulsion table
        create_propulsion_table_query = """
        CREATE TABLE IF NOT EXISTS ferry_propulsion (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ferry_id INT NOT NULL,
            type VARCHAR(100),
            location VARCHAR(50),
            propeller_diameter_mm FLOAT,
            year_manufactured INT,
            FOREIGN KEY (ferry_id) REFERENCES ferries(id) ON DELETE CASCADE
        )
        """
        cursor.execute(create_propulsion_table_query)
        
        connection.commit()
        print("All ferry tables created or already exist")
        
        cursor.close()
        return True
    except Error as e:
        print(f"Error creating ferry tables: {e}")
        return False

def insert_ferry_data(connection, ferry_data):
    """Insert ferry data into the database with proper relational structure"""
    try:
        cursor = connection.cursor()
        
        # First, clear existing data (in reverse order to respect foreign keys)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE ferry_propulsion")
        cursor.execute("TRUNCATE TABLE ferry_engines")
        cursor.execute("TRUNCATE TABLE ferries")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Insert each ferry
        for ferry_name, ferry_info in ferry_data.items():
            # Skip any non-object entries
            if not isinstance(ferry_info, dict):
                continue
                
            # Insert into ferries table
            insert_ferry_query = """
            INSERT INTO ferries (
                name,
                pontos_vessel_id,
                length_over_all_m,
                length_between_perpendiculars_m,
                breadth_m,
                draft_m,
                max_speed_kn,
                installed_power_kw,
                capacity_passenger_car_equivalent,
                gross_tonnage,
                net_tonnage,
                number_of_engines
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            ferry_values = (
                ferry_name,
                ferry_info.get('pontos_vessel_id'),
                ferry_info.get('length_over_all_m'),
                ferry_info.get('length_between_perpendiculars_m'),
                ferry_info.get('breadth_m'),
                ferry_info.get('draft_m'),
                ferry_info.get('max_speed_kn'),
                ferry_info.get('installed_power_kw'),
                ferry_info.get('capacity_passenger_car_equivalent'),
                ferry_info.get('gross_tonnage'),
                ferry_info.get('net_tonnage'),
                ferry_info.get('number_of_engines')
            )
            
            cursor.execute(insert_ferry_query, ferry_values)
            ferry_id = cursor.lastrowid
            
            # Insert engines if they exist
            if 'machinery' in ferry_info and 'engines' in ferry_info['machinery']:
                for engine in ferry_info['machinery']['engines']:
                    insert_engine_query = """
                    INSERT INTO ferry_engines (
                        ferry_id,
                        type,
                        power_kw,
                        rpm,
                        location,
                        year_manufactured
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    
                    engine_values = (
                        ferry_id,
                        engine.get('type'),
                        engine.get('power_kw'),
                        engine.get('rpm'),
                        engine.get('location'),
                        engine.get('year_manufactured')
                    )
                    
                    cursor.execute(insert_engine_query, engine_values)
            
            # Insert propulsion if they exist
            if 'machinery' in ferry_info and 'propulsion' in ferry_info['machinery']:
                for prop in ferry_info['machinery']['propulsion']:
                    insert_propulsion_query = """
                    INSERT INTO ferry_propulsion (
                        ferry_id,
                        type,
                        location,
                        propeller_diameter_mm,
                        year_manufactured
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    
                    propulsion_values = (
                        ferry_id,
                        prop.get('type'),
                        prop.get('location'),
                        prop.get('propeller_diameter_mm'),
                        prop.get('year_manufactured')
                    )
                    
                    cursor.execute(insert_propulsion_query, propulsion_values)
        
        connection.commit()
        print(f"Successfully inserted ferry data with all related components")
        
        cursor.close()
        return True
    except Error as e:
        print(f"Error inserting ferry data: {e}")
        return False

def main():
    """Main function to run the script"""
    # Get the path to ferries.json
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent.parent
    ferries_json_path = project_root / "data" / "ferries.json"
    
    # Load ferry data
    ferry_data = load_json_data(ferries_json_path)
    if not ferry_data:
        print("Failed to load ferry data. Exiting.")
        sys.exit(1)
    
    # Create database connection
    connection = create_connection()
    if not connection:
        print("Failed to connect to the database. Exiting.")
        sys.exit(1)
    
    try:
        # Create ferries table
        if not create_ferries_table(connection):
            print("Failed to create ferries table. Exiting.")
            sys.exit(1)
        
        # Insert ferry data
        if not insert_ferry_data(connection, ferry_data):
            print("Failed to insert ferry data. Exiting.")
            sys.exit(1)
        
        print("Ferry data successfully imported into MySQL database")
    finally:
        # Close the connection
        if connection.is_connected():
            connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    main() 