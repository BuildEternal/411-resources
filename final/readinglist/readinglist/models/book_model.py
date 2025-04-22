import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from readinglist.db import db
from readinglist.utils.logger import configure_logger
from readinglist.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class Books(db.Model):
    """Represents a book in the catalog.

    This model maps to the 'books' table and stores metadata such as author,
    title, genre, release year, and length. It also tracks read count.

    Used in a Flask-SQLAlchemy application for readlist management,
    user interaction, and data-driven book operations.
    """

    __tablename__ = "Books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String, nullable=False)
    length = db.Column(db.Integer, nullable=False)
    read_count = db.Column(db.Integer, nullable=False, default=0)

    def validate(self) -> None:
        """Validates the book instance before committing to the database.

        Raises:
            ValueError: If any required fields are invalid.
        """
        if not self.author or not isinstance(self.author, str):
            raise ValueError("Author must be a non-empty string.")
        if not self.title or not isinstance(self.title, str):
            raise ValueError("Title must be a non-empty string.")
        if not isinstance(self.year, int) or self.year <= 1900:
            raise ValueError("Year must be an integer greater than 1900.")
        if not self.genre or not isinstance(self.genre, str):
            raise ValueError("Genre must be a non-empty string.")
        if not isinstance(self.length, int) or self.length <= 0:
            raise ValueError("Length must be a positive integer.")

    @classmethod
    def create_book(cls, author: str, title: str, year: int, genre: str, length: int) -> None:
        """
        Creates a new book in the books table using SQLAlchemy.

        Args:
            author (str): The author's name.
            title (str): The book title.
            year (int): The year the book was written.
            genre (str): The book genre.
            length (int): The length of the book in pages.

        Raises:
            ValueError: If any field is invalid or if a book with the same compound key already exists.
            SQLAlchemyError: For any other database-related issues.
        """
        logger.info(f"Received request to create book: {author} - {title} ({year})")

        try:
            book = Books(
                author=author.strip(),
                title=title.strip(),
                year=year,
                genre=genre.strip(),
                length=length
            )
            book.validate()
        except ValueError as e:
            logger.warning(f"Validation failed: {e}")
            raise

        try:
            # Check for existing book with same compound key (author, title, year)
            existing = Books.query.filter_by(author=author.strip(), title=title.strip(), year=year).first()
            if existing:
                logger.error(f"Book already exists: {author} - {title} ({year})")
                raise ValueError(f"Book with author '{author}', title '{title}', and year {year} already exists.")

            db.session.add(book)
            db.session.commit()
            logger.info(f"Book successfully added: {author} - {title} ({year})")

        except IntegrityError:
            logger.error(f"Book already exists: {author} - {title} ({year})")
            db.session.rollback()
            raise ValueError(f"Book with author '{author}', title '{title}', and year {year} already exists.")

        except SQLAlchemyError as e:
            logger.error(f"Database error while creating book: {e}")
            db.session.rollback()
            raise

    @classmethod
    def delete_book(cls, book_id: int) -> None:
        """
        Permanently deletes a book from the catalog by ID.

        Args:
            book_id (int): The ID of the book to delete.

        Raises:
            ValueError: If the book with the given ID does not exist.
            SQLAlchemyError: For any database-related issues.
        """
        logger.info(f"Received request to delete book with ID {book_id}")

        try:
            book = db.session.get(cls, book_id)
            if not book:
                logger.warning(f"Attempted to delete non-existent book with ID {book_id}")
                raise ValueError(f"Book with ID {book_id} not found")

            db.session.delete(book)
            db.session.commit()
            logger.info(f"Successfully deleted book with ID {book_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting book with ID {book_id}: {e}")
            db.session.rollback()
            raise

    @classmethod
    def get_book_by_id(cls, book_id: int) -> "Books":
        """
        Retrieves a book from the catalog by its ID.

        Args:
            book_id (int): The ID of the book to retrieve.

        Returns:
            Books: The book instance corresponding to the ID.

        Raises:
            ValueError: If no book with the given ID is found.
            SQLAlchemyError: If a database error occurs.
        """
        logger.info(f"Attempting to retrieve book with ID {book_id}")

        try:
            book = db.session.get(cls, book_id)

            if not book:
                logger.info(f"Book with ID {book_id} not found")
                raise ValueError(f"Book with ID {book_id} not found")

            logger.info(f"Successfully retrieved book: {book.author} - {book.title} ({book.year})")
            return book

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving book by ID {book_id}: {e}")
            raise

    @classmethod
    def get_book_by_compound_key(cls, author: str, title: str, year: int) -> "Books":
        """
        Retrieves a book from the catalog by its compound key (author, title, year).

        Args:
            author (str): The author of the book.
            title (str): The title of the book.
            year (int): The year the book was written.

        Returns:
            Books: The book instance matching the provided compound key.

        Raises:
            ValueError: If no matching book is found.
            SQLAlchemyError: If a database error occurs.
        """
        logger.info(f"Attempting to retrieve book with author '{author}', title '{title}', and year {year}")

        try:
            book = cls.query.filter_by(author=author.strip(), title=title.strip(), year=year).first()

            if not book:
                logger.info(f"Book with author '{author}', title '{title}', and year {year} not found")
                raise ValueError(f"Book with author '{author}', title '{title}', and year {year} not found")

            logger.info(f"Successfully retrieved book: {book.author} - {book.title} ({book.year})")
            return book

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while retrieving book by compound key "
                f"(author '{author}', title '{title}', year {year}): {e}"
            )
            raise

    @classmethod
    def get_all_books(cls, sort_by_read_count: bool = False) -> list[dict]:
        """
        Retrieves all books from the catalog as dictionaries.

        Args:
            sort_by_read_count (bool): If True, sort the books by read count in descending order.

        Returns:
            list[dict]: A list of dictionaries representing all books with read_count.

        Raises:
            SQLAlchemyError: If any database error occurs.
        """
        logger.info("Attempting to retrieve all books from the catalog")

        try:
            query = cls.query
            if sort_by_read_count:
                query = query.order_by(cls.read_count.desc())

            books = query.all()

            if not books:
                logger.warning("The book catalog is empty.")
                return []

            results = [
                {
                    "id": book.id,
                    "author": book.author,
                    "title": book.title,
                    "year": book.year,
                    "genre": book.genre,
                    "length": book.length,
                    "read_count": book.read_count,
                }
                for book in books
            ]

            logger.info(f"Retrieved {len(results)} books from the catalog")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving all books: {e}")
            raise

    @classmethod
    def get_random_book(cls) -> dict:
        """
        Retrieves a random book from the catalog as a dictionary.

        Returns:
            dict: A randomly selected book dictionary.
        """
        all_books = cls.get_all_books()

        if not all_books:
            logger.warning("Cannot retrieve random book because the book catalog is empty.")
            raise ValueError("The book catalog is empty.")

        index = get_random(len(all_books))
        logger.info(f"Random index selected: {index} (total books: {len(all_books)})")

        return all_books[index - 1]

    def update_read_count(self) -> None:
        """
        Increments the read count of the current book instance.

        Raises:
            ValueError: If the book does not exist in the database.
            SQLAlchemyError: If any database error occurs.
        """

        logger.info(f"Attempting to update read count for book with ID {self.id}")

        try:
            book = db.session.get(Books, self.id)
            if not book:
                logger.warning(f"Cannot update read count: Book with ID {self.id} not found.")
                raise ValueError(f"Book with ID {self.id} not found")

            book.read_count += 1
            db.session.commit()

            logger.info(f"Read count incremented for book with ID: {self.id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while updating read count for book with ID {self.id}: {e}")
            db.session.rollback()
            raise
