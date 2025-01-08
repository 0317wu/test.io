import sqlite3
import logging
from datetime import datetime
import os

# Configure logger
logger = logging.getLogger(__name__)

# Database file location
FOOD_RECORD_DB = 'food_record.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(FOOD_RECORD_DB)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initializes the diet records database with necessary tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diet_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                food_item TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
        ''')
        conn.commit()
        conn.close()
        logger.info("Initialized food_record.db with diet_records table.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def save_food_record(user_id, food_items):
    """
    Saves recognized food items into the diet records for the user.

    Parameters:
    - user_id (str): The LINE user ID.
    - food_items (list of str): List of recognized food items.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        for food in food_items:
            cursor.execute('''
                INSERT INTO diet_records (user_id, food_item, timestamp)
                VALUES (?, ?, ?)
            ''', (user_id, food, timestamp))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved food records for user {user_id}: {food_items}")
    except Exception as e:
        logger.error(f"Error saving food records for user {user_id}: {e}")
        raise

def get_diet_records(user_id, limit=10, offset=0):
    """
    Retrieves diet records for a user.

    Parameters:
    - user_id (str): The LINE user ID.
    - limit (int): Number of records to retrieve.
    - offset (int): Number of records to skip.

    Returns:
    - list of dict: List containing diet records.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT food_item, timestamp FROM diet_records
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        rows = cursor.fetchall()
        conn.close()

        records = [{'food_item': row['food_item'], 'timestamp': row['timestamp']} for row in rows]
        logger.info(f"Retrieved {len(records)} diet records for user {user_id}")
        return records
    except Exception as e:
        logger.error(f"Error retrieving diet records for user {user_id}: {e}")
        raise