import logging
import math
from typing import List

from boxing.models.boxers_model import Boxer, update_boxer_stats
from boxing.utils.logger import configure_logger
from boxing.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class RingModel:
    """
    A class to manage a boxing ring for fights between boxers.

    Attributes:
        ring (List[Boxer]): The list of boxers currently in the ring (max 2).
    """

    def __init__(self):
        """
        Initializes the RingModel with an empty ring.
        """
        logger.info("Initializing RingModel with an empty ring")
        self.ring: List[Boxer] = []

    def fight(self) -> str:
        """
        Simulates a fight between two boxers in the ring.

        The fight is decided based on a logistic function of the difference in fighting skills
        and a random factor.

        Returns:
            str: The name of the winning boxer.

        Raises:
            ValueError: If there are fewer than two boxers in the ring.
        """
        logger.info("Initiating fight")
        if len(self.ring) < 2:
            logger.error("Not enough boxers in the ring to start a fight")
            raise ValueError("There must be two boxers to start a fight.")

        boxer_1, boxer_2 = self.get_boxers()
        logger.info(f"Boxers in ring: {boxer_1.name} vs {boxer_2.name}")

        skill_1 = self.get_fighting_skill(boxer_1)
        skill_2 = self.get_fighting_skill(boxer_2)
        logger.info(f"Calculated fighting skills: {boxer_1.name}={skill_1}, {boxer_2.name}={skill_2}")

        # Compute the absolute skill difference and normalize it using a logistic function
        delta = abs(skill_1 - skill_2)
        normalized_delta = 1 / (1 + math.e ** (-delta))
        logger.info(f"Skill delta: {delta}, normalized delta: {normalized_delta}")

        random_number = get_random()
        logger.info(f"Random number generated: {random_number}")

        if random_number < normalized_delta:
            winner = boxer_1
            loser = boxer_2
        else:
            winner = boxer_2
            loser = boxer_1

        logger.info(f"Fight result: {winner.name} wins over {loser.name}")

        update_boxer_stats(winner.id, 'win')
        update_boxer_stats(loser.id, 'loss')
        logger.info(f"Updated stats: {winner.name} recorded a win; {loser.name} recorded a loss")

        self.clear_ring()
        logger.info("Cleared the ring after the fight")

        return winner.name

    def clear_ring(self) -> None:
        """
        Clears all boxers from the ring.
        """
        if not self.ring:
            logger.info("Ring is already empty")
            return
        logger.info("Clearing boxers from the ring")
        self.ring.clear()

    def enter_ring(self, boxer: Boxer) -> None:
        """
        Adds a boxer to the ring.

        Args:
            boxer (Boxer): The boxer to add.

        Raises:
            TypeError: If the provided object is not an instance of Boxer.
            ValueError: If the ring is already full.
        """
        logger.info(f"Attempting to add boxer '{boxer.name}' to the ring")
        if not isinstance(boxer, Boxer):
            logger.error(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'")
            raise TypeError(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'")

        if len(self.ring) >= 2:
            logger.error("Ring is full, cannot add more boxers")
            raise ValueError("Ring is full, cannot add more boxers.")

        self.ring.append(boxer)
        logger.info(f"Boxer '{boxer.name}' successfully entered the ring")

    def get_boxers(self) -> List[Boxer]:
        """
        Retrieves the boxers currently in the ring.

        Returns:
            List[Boxer]: A list of boxers in the ring.
        """
        if not self.ring:
            logger.warning("No boxers in the ring")
        else:
            logger.info(f"Retrieved {len(self.ring)} boxer(s) from the ring")
        return self.ring

    def get_fighting_skill(self, boxer: Boxer) -> float:
        """
        Calculates the fighting skill of a given boxer based on arbitrary factors.

        The calculation factors in the boxer's weight, name length, reach, and age modifier.

        Args:
            boxer (Boxer): The boxer whose fighting skill is to be calculated.

        Returns:
            float: The calculated fighting skill.
        """
        age_modifier = -1 if boxer.age < 25 else (-2 if boxer.age > 35 else 0)
        skill = (boxer.weight * len(boxer.name)) + (boxer.reach / 10) + age_modifier
        logger.info(f"Calculated fighting skill for '{boxer.name}': {skill}")
        return skill
