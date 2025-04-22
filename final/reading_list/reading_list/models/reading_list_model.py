import logging
import os
import time
from typing import List

from final.reading_list.reading_list.models.book_model import Books
from reading_list.utils.api_utils import get_random
from reading_list.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


class ReadingListModel:
    """
    A class to manage a reading list of books.

    """

    def __init__(self):
        """Initializes the ReadingListModel with an empty reading list and the current selection set to 1.

        The reading list is a list of Books, and the current selection number is 1-indexed.
        The TTL (Time To Live) for book caching is set to a default value from the environment variable "TTL",
        which defaults to 60 seconds if not set.

        """
        self.current_selection_number = 1
        self.reading_list: List[int] = []
        self._book_cache: dict[int, Books] = {}
        self._ttl: dict[int, float] = {}
        self.ttl_seconds = int(os.getenv("TTL", 60))  # Default TTL is 60 seconds


    ##################################################
    # Book Management Functions
    ##################################################

    def _get_book_from_cache_or_db(self, book_id: int) -> Books:
        """
        Retrieves a book by ID, using the internal cache if possible.

        This method checks whether a cached version of the book is available
        and still valid. If not, it queries the database, updates the cache, and returns the book.

        Args:
            book_id (int): The unique ID of the book to retrieve.

        Returns:
            Books: The book object corresponding to the given ID.

        Raises:
            ValueError: If the book cannot be found in the database.
        """
        now = time.time()

        if book_id in self._book_cache and self._ttl.get(book_id, 0) > now:
            logger.debug(f"Book ID {book_id} retrieved from cache")
            return self._book_cache[book_id]

        try:
            book = Books.get_book_by_id(book_id)
            logger.info(f"Book ID {book_id} loaded from DB")
        except ValueError as e:
            logger.error(f"Book ID {book_id} not found in DB: {e}")
            raise ValueError(f"Book ID {book_id} not found in database") from e

        self._book_cache[book_id] = book
        self._ttl[book_id] = now + self.ttl_seconds
        return book

    def add_book_to_reading_list(self, book_id: int) -> None:
        """
        Adds a book to the reading list by ID, using the cache or database lookup.

        Args:
            book_id (int): The ID of the book to add to the reading list.

        Raises:
            ValueError: If the book ID is invalid or already exists in the reading list.
        """
        logger.info(f"Received request to add book with ID {book_id} to the reading list")

        book_id = self.validate_book_id(book_id, check_in_reading_list=False)

        if book_id in self.reading_list:
            logger.error(f"Book with ID {book_id} already exists in the reading list")
            raise ValueError(f"Book with ID {book_id} already exists in the reading list")

        try:
            book = self._get_book_from_cache_or_db(book_id)
        except ValueError as e:
            logger.error(f"Failed to add book: {e}")
            raise

        self.reading_list.append(book.id)
        logger.info(f"Successfully added to reading list: {book.author} - {book.title} ({book.year})")


    def remove_book_by_book_id(self, book_id: int) -> None:
        """Removes a book from the reading list by its book ID.

        Args:
            book_id (int): The ID of the book to remove from the reading list.

        Raises:
            ValueError: If the reading list is empty or the book ID is invalid.

        """
        logger.info(f"Received request to remove book with ID {book_id}")

        self.check_if_empty()
        book_id = self.validate_book_id(book_id)

        if book_id not in self.reading_list:
            logger.warning(f"Book with ID {book_id} not found in the reading list")
            raise ValueError(f"Book with ID {book_id} not found in the reading list")

        self.reading_list.remove(book_id)
        logger.info(f"Successfully removed book with ID {book_id} from the reading list")

    def remove_book_by_selection_number(self, selection_number: int) -> None:
        """Removes a book from the reading list by its selection number (1-indexed).

        Args:
            selection_number (int): The selection number of the book to remove.

        Raises:
            ValueError: If the reading list is empty or the selection number is invalid.

        """
        logger.info(f"Received request to remove book at selection number {selection_number}")

        self.check_if_empty()
        selection_number = self.validate_selection_number(selection_number)
        reading_list_index = selection_number - 1

        logger.info(f"Successfully removed book at selection number {selection_number}")
        del self.reading_list[reading_list_index]

    def clear_reading_list(self) -> None:
        """Clears all books from the reading list.

        Clears all books from the reading list. If the reading list is already empty, logs a warning.

        """
        logger.info("Received request to clear the reading list")

        try:
            if self.check_if_empty():
                pass
        except ValueError:
            logger.warning("Clearing an empty reading list")

        self.reading_list.clear()
        logger.info("Successfully cleared the reading list")


    ##################################################
    # Reading List Retrieval Functions
    ##################################################


    def get_all_books(self) -> List[Books]:
        """Returns a list of all books in the reading list using cached book data.

        Returns:
            List[Books]: A list of all books in the reading list.

        Raises:
            ValueError: If the reading list is empty.
        """
        self.check_if_empty()
        logger.info("Retrieving all books in the reading list")
        return [self._get_book_from_cache_or_db(book_id) for book_id in self.reading_list]

    def get_book_by_book_id(self, book_id: int) -> Books:
        """Retrieves a book from the reading list by its book ID using the cache or DB.

        Args:
            book_id (int): The ID of the book to retrieve.

        Returns:
            Books: The book with the specified ID.

        Raises:
            ValueError: If the reading list is empty or the book is not found.
        """
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)
        logger.info(f"Retrieving book with ID {book_id} from the reading list")
        book = self._get_book_from_cache_or_db(book_id)
        logger.info(f"Successfully retrieved book: {book.author} - {book.title} ({book.year})")
        return book

    def get_book_by_selection_number(self, selection_number: int) -> Books:
        """Retrieves a book from the reading list by its selection number (1-indexed).

        Args:
            selection_number (int): The selection number of the book to retrieve.

        Returns:
            Books: The book at the specified selection number.

        Raises:
            ValueError: If the reading list is empty or the selection number is invalid.
        """
        self.check_if_empty()
        selection_number = self.validate_selection_number(selection_number)
        reading_list_index = selection_number - 1

        logger.info(f"Retrieving book at selection number {selection_number} from reading list")
        book_id = self.reading_list[reading_list_index]
        book = self._get_book_from_cache_or_db(book_id)
        logger.info(f"Successfully retrieved book: {book.author} - {book.title} ({book.year})")
        return book

    def get_current_book(self) -> Books:
        """Returns the current book being read.

        Returns:
            Books: The currently being read book.

        Raises:
            ValueError: If the reading list is empty.
        """
        self.check_if_empty()
        logger.info("Retrieving the current book being read")
        return self.get_book_by_selection_number(self.current_selection_number)

    def get_reading_list_length(self) -> int:
        """Returns the number of books in the reading list.

        Returns:
            int: The total number of books in the reading list.

        """
        length = len(self.reading_list)
        logger.info(f"Retrieving reading list length: {length} books")
        return length

    def get_reading_list_length(self) -> int:
        """
        Returns the total length of the reading list in pages using cached books.

        Returns:
            int: The total length of all books in the reading list in pages.
        """
        total_length = sum(self._get_book_from_cache_or_db(book_id).length for book_id in self.reading_list)
        logger.info(f"Retrieving total reading list length: {total_length} pages")
        return total_length


    ##################################################
    # Reading list Movement Functions
    ##################################################


    def go_to_selection_number(self, selection_number: int) -> None:
        """Sets the current selection number to the specified selection number.

        Args:
            selection_number (int): The selection number to set as the current selection.

        Raises:
            ValueError: If the reading list is empty or the selection number is invalid.

        """
        self.check_if_empty()
        selection_number = self.validate_selection_number(selection_number)
        logger.info(f"Setting current selection number to {selection_number}")
        self.current_selection_number = selection_number

    def go_to_random_selection(self) -> None:
        """Sets the current selection number to a randomly selected selection.

        Raises:
            ValueError: If the reading list is empty.

        """
        self.check_if_empty()

        # Get a random index using the random.org API
        random_selection = get_random(self.get_reading_list_length())

        logger.info(f"Setting current selection number to random selection: {random_selection}")
        self.current_selection_number = random_selection

    def move_book_to_beginning(self, book_id: int) -> None:
        """Moves a book to the beginning of the reading list.

        Args:
            book_id (int): The ID of the book to move.

        Raises:
            ValueError: If the reading list is empty or the book ID is invalid.

        """
        logger.info(f"Moving book with ID {book_id} to the beginning of the reading list")
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)

        self.reading_list.remove(book_id)
        self.reading_list.insert(0, book_id)

        logger.info(f"Successfully moved book with ID {book_id} to the beginning")

    def move_book_to_end(self, book_id: int) -> None:
        """Moves a book to the end of the reading list.

        Args:
            book_id (int): The ID of the book to move.

        Raises:
            ValueError: If the reading list is empty or the book ID is invalid.

        """
        logger.info(f"Moving book with ID {book_id} to the end of the reading list")
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)

        self.reading_list.remove(book_id)
        self.reading_list.append(book_id)

        logger.info(f"Successfully moved book with ID {book_id} to the end")

    def move_book_to_selection_number(self, book_id: int, selection_number: int) -> None:
        """Moves a book to a specific selection number in the reading list.

        Args:
            book_id (int): The ID of the book to move.
            selection_number (int): The selection number to move the book to (1-indexed).

        Raises:
            ValueError: If the reading list is empty, the book ID is invalid, or the selection number is out of range.

        """
        logger.info(f"Moving book with ID {book_id} to selection number {selection_number}")
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)
        selection_number = self.validate_selection_number(selection_number)

        reading_list_index = selection_number - 1

        self.reading_list.remove(book_id)
        self.reading_list.insert(reading_list_index, book_id)

        logger.info(f"Successfully moved book with ID {book_id} to selection number {selection_number}")

    def swap_books_in_reading_list(self, book1_id: int, book2_id: int) -> None:
        """Swaps the positions of two books in the reading list.

        Args:
            book1_id (int): The ID of the first book to swap.
            book2_id (int): The ID of the second book to swap.

        Raises:
            ValueError: If the reading list is empty, either book ID is invalid, or attempting to swap the same book.

        """
        logger.info(f"Swapping books with IDs {book1_id} and {book2_id}")
        self.check_if_empty()
        book1_id = self.validate_book_id(book1_id)
        book2_id = self.validate_book_id(book2_id)

        if book1_id == book2_id:
            logger.error(f"Cannot swap a book with itself: {book1_id}")
            raise ValueError(f"Cannot swap a book with itself: {book1_id}")

        index1, index2 = self.reading_list.index(book1_id), self.reading_list.index(book2_id)

        self.reading_list[index1], self.reading_list[index2] = self.reading_list[index2], self.reading_list[index1]

        logger.info(f"Successfully swapped books with IDs {book1_id} and {book2_id}")


    ##################################################
    # Reading List Reading Functions
    ##################################################


    def read_current_book(self) -> None:
        """Reads the current book and advances the reading list.

        Raises:
            ValueError: If the reading list is empty.

        """
        self.check_if_empty()
        current_book = self.get_book_by_selection_number(self.current_selection_number)

        logger.info(f"Reading book: {current_book.title} (ID: {current_book.id}) at selection number: {self.current_selection_number}")
        current_book.update_read_count()
        logger.info(f"Updated read count for book: {current_book.title} (ID: {current_book.id})")

        self.current_selection_number = (self.current_selection_number % self.get_reading_list_length()) + 1
        logger.info(f"Advanced to selection number: {self.current_selection_number}")

    def read_entire_reading_list(self) -> None:
        """Reads all books in the reading list from the beginning.

        Raises:
            ValueError: If the reading list is empty.

        """
        self.check_if_empty()
        logger.info("Starting to read the entire reading list.")

        self.current_selection_number = 1
        for _ in range(self.get_reading_list_length()):
            self.read_current_book()

        logger.info("Finished reading the entire reading list.")

    def read_rest_of_reading_list(self) -> None:
        """Reads the remaining books in the reading list from the current selection onward.

        Raises:
            ValueError: If the reading list is empty.

        """
        self.check_if_empty()
        logger.info(f"Reading the rest of the reading list from selection number: {self.current_selection_number}")

        for _ in range(self.get_reading_list_length() - self.current_selection_number + 1):
            self.read_current_book()

        logger.info("Finished reading the rest of the reading list.")

    def rewind_reading_list(self) -> None:
        """Resets the reading list to the first selection.

        Raises:
            ValueError: If the reading list is empty.

        """
        self.check_if_empty()
        self.current_selection_number = 1
        logger.info("Rewound reading list to the first selection.")


    ##################################################
    # Utility Functions
    ##################################################


    ####################################################################################################
    #
    # Note: I am only testing these things once. EG I am not testing that everything rejects an empty
    # list as they all do so by calling this helper
    #
    ####################################################################################################

    def validate_book_id(self, book_id: int, check_in_reading_list: bool = True) -> int:
        """
        Validates the given book ID.

        Args:
            book_id (int): The book ID to validate.
            check_in_reading_list (bool, optional): If True, verifies the ID is present in the reading list.
                                                    If False, skips that check. Defaults to True.

        Returns:
            int: The validated book ID.

        Raises:
            ValueError: If the book ID is not a non-negative integer,
                        not found in the reading list (if check_in_reading_list=True),
                        or not found in the database.
        """
        try:
            book_id = int(book_id)
            if book_id < 0:
                raise ValueError
        except ValueError:
            logger.error(f"Invalid book id: {book_id}")
            raise ValueError(f"Invalid book id: {book_id}")

        if check_in_reading_list and book_id not in self.reading_list:
            logger.error(f"Book with id {book_id} not found in reading list")
            raise ValueError(f"Book with id {book_id} not found in reading list")

        try:
            self._get_book_from_cache_or_db(book_id)
        except Exception as e:
            logger.error(f"Book with id {book_id} not found in database: {e}")
            raise ValueError(f"Book with id {book_id} not found in database")

        return book_id

    def validate_selection_number(self, selection_number: int) -> int:
        """
        Validates the given selection number, ensuring it is within the reading list's range.

        Args:
            selection_number (int): The selection number to validate.

        Returns:
            int: The validated selection number.

        Raises:
            ValueError: If the selection number is not a valid positive integer or is out of range.

        """
        try:
            selection_number = int(selection_number)
            if not (1 <= selection_number <= self.get_reading_list_length()):
                raise ValueError(f"Invalid selection number: {selection_number}")
        except ValueError as e:
            logger.error(f"Invalid selection number: {selection_number}")
            raise ValueError(f"Invalid selection number: {selection_number}") from e

        return selection_number

    def check_if_empty(self) -> None:
        """
        Checks if the reading list is empty and raises a ValueError if it is.

        Raises:
            ValueError: If the reading list is empty.

        """
        if not self.reading_list:
            logger.error("Reading list is empty")
            raise ValueError("Reading list is empty")
