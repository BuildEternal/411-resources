import math
import pytest

from boxing.models.ring_model import RingModel
from boxing.models.boxers_model import Boxer, update_boxer_stats


@pytest.fixture
def ring_model():
    """Fixture to provide a new RingModel instance for each test."""
    return RingModel()


@pytest.fixture
def sample_boxer1():
    """
    Returns a sample boxer.
    Attributes: id, name, weight, height, reach, age.
    Example: Mike Tyson, weight=220, height=70, reach=75, age=30.
    """
    return Boxer(1, "Mike Tyson", 220, 70, 75, 30)


@pytest.fixture
def sample_boxer2():
    """
    Returns a sample boxer.
    Example: Muhammad Ali, weight=190, height=75, reach=80, age=35.
    """
    return Boxer(2, "Muhammad Ali", 190, 75, 80, 35)


@pytest.fixture
def sample_boxer3():
    """
    Returns a sample boxer.
    Example: Rocky Balboa, weight=210, height=72, reach=78, age=28.
    """
    return Boxer(3, "Rocky Balboa", 210, 72, 78, 28)


def test_enter_ring_success(ring_model, sample_boxer1):
    """Test adding a boxer to the ring."""
    ring_model.enter_ring(sample_boxer1)
    assert len(ring_model.ring) == 1
    assert ring_model.ring[0].name == sample_boxer1.name


def test_enter_ring_full(ring_model, sample_boxer1, sample_boxer2, sample_boxer3):
    """Test error when adding a boxer to a full ring."""
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)
    with pytest.raises(ValueError, match="Ring is full, cannot add more boxers"):
        ring_model.enter_ring(sample_boxer3)


def test_get_boxers(ring_model, sample_boxer1, sample_boxer2):
    """Test retrieving boxers from the ring."""
    # Initially empty
    boxers = ring_model.get_boxers()
    assert isinstance(boxers, list)
    assert len(boxers) == 0

    # After adding boxers
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)
    boxers = ring_model.get_boxers()
    assert len(boxers) == 2


def test_clear_ring(ring_model, sample_boxer1, sample_boxer2):
    """Test that clear_ring empties the ring."""
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)
    assert len(ring_model.ring) == 2
    ring_model.clear_ring()
    assert len(ring_model.ring) == 0


def test_get_fighting_skill(ring_model, sample_boxer1):
    """
    Test calculation of fighting skill.
    Calculation:
        skill = (boxer.weight * len(boxer.name)) + (boxer.reach / 10) + age_modifier
    where age_modifier = -1 if age < 25, -2 if age > 35, else 0.
    """
    # For sample_boxer1: "Mike Tyson" length is calculated including the space.
    # Age is 30 so age_modifier = 0.
    expected_skill = (sample_boxer1.weight * len(sample_boxer1.name)) + (sample_boxer1.reach / 10)
    calculated_skill = ring_model.get_fighting_skill(sample_boxer1)
    assert math.isclose(calculated_skill, expected_skill)


def test_fight_success(ring_model, sample_boxer1, sample_boxer2, monkeypatch):
    """
    Test the fight function.
    We control randomness by patching get_random to return a fixed value.
    We also patch update_boxer_stats to avoid side effects.
    """
    # Patch get_random from boxing.models.ring_model to return 0.0
    monkeypatch.setattr("boxing.models.ring_model.get_random", lambda: 0.0)
    # Patch update_boxer_stats to do nothing
    monkeypatch.setattr("boxing.models.ring_model.update_boxer_stats", lambda boxer_id, result: None)

    # Add two boxers to the ring.
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)

    # With get_random returning 0.0, the normalized delta (which is > 0) will result in boxer_1 winning.
    winner_name = ring_model.fight()
    assert winner_name == sample_boxer1.name
    # The ring should be cleared after the fight.
    assert len(ring_model.ring) == 0


def test_fight_insufficient_boxers(ring_model, sample_boxer1):
    """Test that fight() raises ValueError when there are fewer than two boxers."""
    ring_model.enter_ring(sample_boxer1)
    with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
        ring_model.fight()
