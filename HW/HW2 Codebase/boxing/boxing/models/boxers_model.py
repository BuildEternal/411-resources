from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Boxer:
    """
    Data class representing a boxer.

    Attributes:
        id (int): Unique identifier for the boxer.
        name (str): The boxer's name.
        weight (int): The boxer's weight in pounds.
        height (int): The boxer's height in inches.
        reach (float): The boxer's reach in inches.
        age (int): The boxer's age.
        weight_class (str): The boxer's weight class (assigned automatically).
    """
    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

    def __post_init__(self):
        """Assigns the weight class based on the boxer's weight."""
        self.weight_class = get_weight_class(self.weight)


def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None:
    """
    Creates a new boxer record in the database.

    Args:
        name (str): The name of the boxer.
        weight (int): The weight of the boxer.
        height (int): The height of the boxer.
        reach (float): The reach of the boxer.
        age (int): The age of the boxer.

    Raises:
        ValueError: If any parameter is invalid or a boxer with the same name exists.
        sqlite3.Error: If a database error occurs.
    """
    logger.info(f"Received request to create boxer: {name}")
    if weight < 125:
        logger.error(f"Invalid weight: {weight}. Must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.error(f"Invalid height: {height}. Must be greater than 0.")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.error(f"Invalid reach: {reach}. Must be greater than 0.")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.error(f"Invalid age: {age}. Must be between 18 and 40.")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger.info(f"Checking if boxer with name '{name}' already exists")
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                logger.error(f"Boxer with name '{name}' already exists")
                raise ValueError(f"Boxer with name '{name}' already exists")

            logger.info(f"Inserting boxer '{name}' into database")
            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()
            logger.info(f"Successfully created boxer: {name}")

    except sqlite3.IntegrityError:
        logger.error(f"Boxer with name '{name}' already exists (IntegrityError)")
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        logger.error(f"Database error when creating boxer '{name}': {e}")
        raise e


def delete_boxer(boxer_id: int) -> None:
    """
    Deletes a boxer record from the database by boxer ID.

    Args:
        boxer_id (int): The unique ID of the boxer to delete.

    Raises:
        ValueError: If the boxer is not found.
        sqlite3.Error: If a database error occurs.
    """
    logger.info(f"Received request to delete boxer with ID {boxer_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.error(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            logger.info(f"Deleting boxer with ID {boxer_id}")
            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()
            logger.info(f"Successfully deleted boxer with ID {boxer_id}")

    except sqlite3.Error as e:
        logger.error(f"Database error when deleting boxer with ID {boxer_id}: {e}")
        raise e


def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]:
    """
    Retrieves a leaderboard of boxers sorted by wins or win percentage.

    Args:
        sort_by (str): The sorting criteria, either "wins" or "win_pct". Defaults to "wins".

    Returns:
        List[dict[str, Any]]: A list of dictionaries representing boxer stats.

    Raises:
        ValueError: If an invalid sort_by parameter is provided.
        sqlite3.Error: If a database error occurs.
    """
    logger.info(f"Retrieving leaderboard sorted by {sort_by}")
    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.error(f"Invalid sort_by parameter: {sort_by}")
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info("Successfully retrieved leaderboard data")

        leaderboard = []
        for row in rows:
            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        logger.info("Formatted leaderboard data successfully")
        return leaderboard

    except sqlite3.Error as e:
        logger.error(f"Database error when retrieving leaderboard: {e}")
        raise e


def get_boxer_by_id(boxer_id: int) -> Boxer:
    """
    Retrieves a boxer record from the database by boxer ID.

    Args:
        boxer_id (int): The unique ID of the boxer.

    Returns:
        Boxer: A Boxer object representing the boxer.

    Raises:
        ValueError: If the boxer is not found.
        sqlite3.Error: If a database error occurs.
    """
    logger.info(f"Retrieving boxer with ID {boxer_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))
            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Successfully retrieved boxer with ID {boxer_id}")
                return boxer
            else:
                logger.error(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error when retrieving boxer with ID {boxer_id}: {e}")
        raise e


def get_boxer_by_name(boxer_name: str) -> Boxer:
    """
    Retrieves a boxer record from the database by boxer name.

    Args:
        boxer_name (str): The name of the boxer.

    Returns:
        Boxer: A Boxer object representing the boxer.

    Raises:
        ValueError: If the boxer is not found.
        sqlite3.Error: If a database error occurs.
    """
    logger.info(f"Retrieving boxer with name '{boxer_name}'")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))
            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Successfully retrieved boxer '{boxer_name}'")
                return boxer
            else:
                logger.error(f"Boxer '{boxer_name}' not found.")
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error when retrieving boxer '{boxer_name}': {e}")
        raise e


def get_weight_class(weight: int) -> str:
    """
    Determines the weight class for a given weight.

    Args:
        weight (int): The weight of the boxer.

    Returns:
        str: The weight class.

    Raises:
        ValueError: If the weight is less than 125.
    """
    logger.info(f"Determining weight class for weight: {weight}")
    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        logger.error(f"Invalid weight: {weight}. Weight must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")

    logger.info(f"Determined weight class: {weight_class}")
    return weight_class


def update_boxer_stats(boxer_id: int, result: str) -> None:
    """
    Updates the statistics of a boxer based on the result of a fight.

    Args:
        boxer_id (int): The unique ID of the boxer.
        result (str): The outcome of the fight, either 'win' or 'loss'.

    Raises:
        ValueError: If the result is invalid or the boxer is not found.
        sqlite3.Error: If a database error occurs.
    """
    logger.info(f"Updating stats for boxer with ID {boxer_id} for result '{result}'")
    if result not in {'win', 'loss'}:
        logger.error(f"Invalid result: {result}. Expected 'win' or 'loss'.")
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.error(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                logger.info(f"Incrementing wins and fights for boxer ID {boxer_id}")
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:  # result == 'loss'
                logger.info(f"Incrementing fights for boxer ID {boxer_id} (loss)")
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()
            logger.info(f"Successfully updated stats for boxer with ID {boxer_id}")

    except sqlite3.Error as e:
        logger.error(f"Database error when updating stats for boxer with ID {boxer_id}: {e}")
        raise e
