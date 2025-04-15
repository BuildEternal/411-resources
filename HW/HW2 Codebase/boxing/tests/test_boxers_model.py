import sqlite3
import pytest
import math

from boxing.models import boxers_model as bm
from boxing.models.boxers_model import Boxer, get_weight_class

# Fixture to provide an in-memory SQLite database and create the "boxers" table.
@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE boxers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            weight INTEGER,
            height INTEGER,
            reach REAL,
            age INTEGER,
            fights INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    yield conn
    conn.close()

# Automatically patch get_db_connection in boxers_model to return our in-memory db.
@pytest.fixture(autouse=True)
def patch_db_connection(monkeypatch, db_conn):
    monkeypatch.setattr(bm, "get_db_connection", lambda: db_conn)

########################################
# Tests for get_weight_class
########################################

def test_get_weight_class_heavyweight():
    # Weight >= 203 should return HEAVYWEIGHT.
    assert get_weight_class(210) == "HEAVYWEIGHT"

def test_get_weight_class_middleweight():
    # Weight in [166,202] should return MIDDLEWEIGHT.
    assert get_weight_class(170) == "MIDDLEWEIGHT"

def test_get_weight_class_lightweight():
    # Weight in [133,165] should return LIGHTWEIGHT.
    assert get_weight_class(140) == "LIGHTWEIGHT"

def test_get_weight_class_featherweight():
    # Weight in [125,132] should return FEATHERWEIGHT.
    assert get_weight_class(130) == "FEATHERWEIGHT"

def test_get_weight_class_invalid():
    with pytest.raises(ValueError, match="Invalid weight: 120. Weight must be at least 125."):
        get_weight_class(120)

########################################
# Tests for create_boxer
########################################

def test_create_boxer_success(db_conn):
    # Create a boxer successfully.
    bm.create_boxer("Test Boxer", 150, 70, 70.0, 25)
    cursor = db_conn.cursor()
    cursor.execute("SELECT name, weight, height, reach, age FROM boxers WHERE name = ?", ("Test Boxer",))
    row = cursor.fetchone()
    assert row is not None
    name, weight, height, reach, age = row
    assert name == "Test Boxer"
    assert weight == 150
    assert height == 70
    assert math.isclose(reach, 70.0)
    assert age == 25

def test_create_boxer_invalid_weight():
    with pytest.raises(ValueError, match="Invalid weight: 120. Must be at least 125."):
        bm.create_boxer("Test Boxer", 120, 70, 70.0, 25)

def test_create_boxer_invalid_height():
    with pytest.raises(ValueError, match="Invalid height: 0. Must be greater than 0."):
        bm.create_boxer("Test Boxer", 150, 0, 70.0, 25)

def test_create_boxer_invalid_reach():
    with pytest.raises(ValueError, match="Invalid reach: 0. Must be greater than 0."):
        bm.create_boxer("Test Boxer", 150, 70, 0, 25)

def test_create_boxer_invalid_age():
    with pytest.raises(ValueError, match="Invalid age: 17. Must be between 18 and 40."):
        bm.create_boxer("Test Boxer", 150, 70, 70.0, 17)

def test_create_boxer_duplicate(db_conn):
    bm.create_boxer("Unique Boxer", 150, 70, 70.0, 25)
    with pytest.raises(ValueError, match="Boxer with name 'Unique Boxer' already exists"):
        bm.create_boxer("Unique Boxer", 155, 72, 71.0, 26)

########################################
# Tests for delete_boxer
########################################

def test_delete_boxer_success(db_conn):
    bm.create_boxer("Delete Boxer", 160, 72, 72.0, 30)
    cursor = db_conn.cursor()
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("Delete Boxer",))
    boxer_id = cursor.fetchone()[0]
    bm.delete_boxer(boxer_id)
    cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
    assert cursor.fetchone() is None

def test_delete_boxer_not_found():
    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        bm.delete_boxer(999)

########################################
# Tests for get_boxer_by_id and get_boxer_by_name
########################################

def test_get_boxer_by_id(db_conn):
    bm.create_boxer("ID Boxer", 155, 68, 68.0, 28)
    cursor = db_conn.cursor()
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("ID Boxer",))
    boxer_id = cursor.fetchone()[0]
    boxer = bm.get_boxer_by_id(boxer_id)
    assert isinstance(boxer, Boxer)
    assert boxer.name == "ID Boxer"
    assert boxer.weight == 155

def test_get_boxer_by_id_not_found():
    with pytest.raises(ValueError, match="Boxer with ID 888 not found."):
        bm.get_boxer_by_id(888)

def test_get_boxer_by_name(db_conn):
    bm.create_boxer("Name Boxer", 165, 69, 69.0, 27)
    boxer = bm.get_boxer_by_name("Name Boxer")
    assert isinstance(boxer, Boxer)
    assert boxer.name == "Name Boxer"
    assert boxer.height == 69

def test_get_boxer_by_name_not_found():
    with pytest.raises(ValueError, match="Boxer 'Nonexistent Boxer' not found."):
        bm.get_boxer_by_name("Nonexistent Boxer")

########################################
# Tests for update_boxer_stats
########################################

def test_update_boxer_stats_win(db_conn):
    bm.create_boxer("Stat Boxer", 170, 70, 70.0, 29)
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, fights, wins FROM boxers WHERE name = ?", ("Stat Boxer",))
    boxer_id, fights, wins = cursor.fetchone()
    assert fights == 0 and wins == 0

    bm.update_boxer_stats(boxer_id, "win")
    cursor.execute("SELECT fights, wins FROM boxers WHERE id = ?", (boxer_id,))
    fights, wins = cursor.fetchone()
    assert fights == 1 and wins == 1

def test_update_boxer_stats_loss(db_conn):
    bm.create_boxer("Loss Boxer", 175, 71, 71.0, 30)
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, fights, wins FROM boxers WHERE name = ?", ("Loss Boxer",))
    boxer_id, fights, wins = cursor.fetchone()
    assert fights == 0 and wins == 0

    bm.update_boxer_stats(boxer_id, "loss")
    cursor.execute("SELECT fights, wins FROM boxers WHERE id = ?", (boxer_id,))
    fights, wins = cursor.fetchone()
    assert fights == 1 and wins == 0

def test_update_boxer_stats_invalid_result(db_conn):
    bm.create_boxer("Invalid Result Boxer", 180, 72, 72.0, 31)
    cursor = db_conn.cursor()
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("Invalid Result Boxer",))
    boxer_id = cursor.fetchone()[0]
    with pytest.raises(ValueError, match="Invalid result: draw. Expected 'win' or 'loss'."):
        bm.update_boxer_stats(boxer_id, "draw")

def test_update_boxer_stats_boxer_not_found():
    with pytest.raises(ValueError, match="Boxer with ID 777 not found."):
        bm.update_boxer_stats(777, "win")

########################################
# Tests for get_leaderboard
########################################

def test_get_leaderboard_sort_by_wins(db_conn):
    # Create two boxers and update their stats:
    bm.create_boxer("Boxer A", 160, 68, 68.0, 26)
    bm.create_boxer("Boxer B", 165, 69, 69.0, 27)
    cursor = db_conn.cursor()
    # Retrieve their IDs
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("Boxer A",))
    boxer_a_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("Boxer B",))
    boxer_b_id = cursor.fetchone()[0]

    # Boxer A: 2 wins (2 fights), Boxer B: 1 win (1 fight)
    bm.update_boxer_stats(boxer_a_id, "win")
    bm.update_boxer_stats(boxer_a_id, "win")
    bm.update_boxer_stats(boxer_b_id, "win")

    leaderboard = bm.get_leaderboard("wins")
    # Leaderboard should be sorted with Boxer A first.
    assert leaderboard[0]["name"] == "Boxer A"
    assert leaderboard[0]["wins"] == 2
    assert leaderboard[1]["name"] == "Boxer B"
    assert leaderboard[1]["wins"] == 1

def test_get_leaderboard_sort_by_win_pct(db_conn):
    # Create three boxers and update stats
    bm.create_boxer("Boxer X", 170, 70, 70.0, 28)
    bm.create_boxer("Boxer Y", 175, 71, 71.0, 29)
    bm.create_boxer("Boxer Z", 180, 72, 72.0, 30)
    cursor = db_conn.cursor()
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("Boxer X",))
    boxer_x_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("Boxer Y",))
    boxer_y_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM boxers WHERE name = ?", ("Boxer Z",))
    boxer_z_id = cursor.fetchone()[0]

    # Boxer X: 3 wins out of 3 fights => win_pct = 1.0
    # Boxer Y: 1 win out of 3 fights => win_pct ~ 0.333
    # Boxer Z: 2 wins out of 3 fights => win_pct ~ 0.667
    for _ in range(3):
        bm.update_boxer_stats(boxer_x_id, "win")
    for _ in range(2):
        bm.update_boxer_stats(boxer_y_id, "loss")
    bm.update_boxer_stats(boxer_y_id, "win")
    bm.update_boxer_stats(boxer_z_id, "win")
    bm.update_boxer_stats(boxer_z_id, "loss")
    bm.update_boxer_stats(boxer_z_id, "win")

    leaderboard = bm.get_leaderboard("win_pct")
    # Leaderboard should be sorted with highest win_pct first.
    # Boxer X win_pct = 100.0, Boxer Z ~66.7, Boxer Y ~33.3.
    assert leaderboard[0]["name"] == "Boxer X"
    assert math.isclose(leaderboard[0]["win_pct"], 100.0)
    assert leaderboard[1]["name"] == "Boxer Z"
    assert leaderboard[2]["name"] == "Boxer Y"

def test_get_leaderboard_invalid_sort_by(db_conn):
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        bm.get_leaderboard("invalid")
