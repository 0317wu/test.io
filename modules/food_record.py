Okay, the human wants to add a new database to track food intake and calculate calorie consumption. This is a great addition that aligns perfectly with the fitness theme of the bot. This will involve:
1. Designing a new database schema.
2. Creating new database interaction functions.
3. Integrating these functions with the bot's message handling logic.

Let's start by designing the new database schema. I'll need a table to store food items, the number of servings, and the timestamp when they were eaten by a specific user. Here's the structure I envision:

`food_entries` table:
*   `id` INTEGER PRIMARY KEY AUTOINCREMENT - Unique identifier for each entry.
*   `user_id` TEXT NOT NULL -  LINE user ID of the person who ate the food.
*   `food_name` TEXT NOT NULL - Name of the food item.
*   `servings` REAL NOT NULL - Number of servings (could be a decimal for fractional servings).
*   `calories_per_serving` REAL NOT NULL - Calories per serving for a given food.
*   `timestamp` INTEGER NOT NULL - Timestamp of when the food was consumed (Unix timestamp).
*   `entry_date` TEXT NOT NULL -  Date of the food entry, in "YYYY-MM-DD" format

Additionally, I need a `food_reference` table, that stores common food information.

`food_reference` table:
*   `food_name` TEXT PRIMARY KEY - Name of the food item.
*   `calories_per_serving` REAL NOT NULL - Calories per serving for a given food.

Now, let's outline the database interaction functions that I need to write:

*   `create_food_database(database_path)`: Creates the database and the necessary tables, if they don't exist.
*   `add_food_entry(database_path, user_id, food_name, servings, calories_per_serving, timestamp, entry_date)`: Adds a new food entry to the database.
*   `get_food_entries(database_path, user_id, date)`: Fetches all food entries for a given user on a specific date.
*  `get_food_calories(database_path, user_id, date)`: Calculate the total calories consumed by the user for a specific date.
*   `add_food_reference(database_path, food_name, calories_per_serving)`: Adds a new food reference with calorie information.
*   `get_food_reference(database_path, food_name)`: Get the food reference from `food_reference` table.

I will need to modify the bot's `handle_message` function to support:
*   Adding food entries by prompting the user for the food name, servings and date. The system will automatically calculate the total calories using information from `food_reference` table.
*   Displaying the calorie consumption for a specific day.

Now, let me incorporate these changes into the human's code, reusing the existing modules and logic. I will add new functions in `modules/food_record.py`, then include this module in `app.py`. I also need to modify `app.py` to use these new functions.

First, here's the `modules/food_record.py`:
```python
import sqlite3
import logging
import datetime

logger = logging.getLogger(__name__)
# Database interaction functions

def get_db_connection(database_path):
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn


def create_food_database(database_path):
    """Creates the food database and tables if they don't exist."""
    try:
        with get_db_connection(database_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS food_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    food_name TEXT NOT NULL,
                    servings REAL NOT NULL,
                    calories_per_serving REAL NOT NULL,
                    timestamp INTEGER NOT NULL,
                    entry_date TEXT NOT NULL
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS food_reference (
                    food_name TEXT PRIMARY KEY,
                    calories_per_serving REAL NOT NULL
                )
            ''')
            logger.info("Food database and tables created (or already exist).")
    except Exception as e:
        logger.error(f"Error creating food database: {e}")


def add_food_entry(database_path, user_id, food_name, servings, calories_per_serving, timestamp, entry_date):
    """Adds a new food entry to the database."""
    try:
        with get_db_connection(database_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO food_entries (user_id, food_name, servings, calories_per_serving, timestamp, entry_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, food_name, servings, calories_per_serving, timestamp, entry_date))
            logger.info(f"Added food entry: {user_id}, {food_name}, {servings}, {calories_per_serving}, {timestamp}, {entry_date}")
    except Exception as e:
        logger.error(f"Error adding food entry: {e}")


def get_food_entries(database_path, user_id, date):
    """Fetches all food entries for a given user on a specific date."""
    try:
        with get_db_connection(database_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT food_name, servings, calories_per_serving, timestamp FROM food_entries
                WHERE user_id = ? AND entry_date = ? ORDER BY timestamp ASC
            ''', (user_id, date))
            rows = c.fetchall()
            logger.info(f"Retrieved food entries for user {user_id} on date {date}. Found {len(rows)} entries.")
            return rows
    except Exception as e:
        logger.error(f"Error fetching food entries: {e}")
        return []


def get_food_calories(database_path, user_id, date):
    """Calculates the total calories consumed by a user on a specific date."""
    entries = get_food_entries(database_path, user_id, date)
    total_calories = sum(entry['servings'] * entry['calories_per_serving'] for entry in entries)
    logger.info(f"Calculated total calories {total_calories} for user {user_id} on date {date}")
    return total_calories


def add_food_reference(database_path, food_name, calories_per_serving):
    """Adds a food item and its calorie count to the food_reference table."""
    try:
        with get_db_connection(database_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO food_reference (food_name, calories_per_serving)
                VALUES (?, ?)
            ''', (food_name, calories_per_serving))
            logger.info(f"Added food reference: {food_name}, {calories_per_serving}")
    except Exception as e:
         logger.error(f"Error adding food reference {food_name} to database: {e}")

def get_food_reference(database_path, food_name):
    """Retrieves the calorie count of a food item from the database."""
    try:
        with get_db_connection(database_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT calories_per_serving FROM food_reference
                WHERE food_name = ?
            ''', (food_name,))
            row = c.fetchone()
            if row:
                logger.info(f"Found food reference: {food_name} with {row['calories_per_serving']} calories.")
                return row['calories_per_serving']
            else:
                logger.info(f"No food reference found for: {food_name}")
                return None
    except Exception as e:
        logger.error(f"Error getting food reference for {food_name}: {e}")
        return None