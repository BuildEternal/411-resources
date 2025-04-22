import pytest

from readinglist.models.book_model import Books


# --- Fixtures ---

@pytest.fixture
def book_mockingbird(session):
    """Fixture for "To Kill a Mockingbird" by Harper Lee."""
    book = Books(
        author="Harper Lee",
        title="To Kill a Mockingbird",
        year=1960,
        genre="Southern Gothic",
        length=281
    )
    session.add(book)
    session.commit()
    return book

@pytest.fixture
def book_1984(session):
    """Fixture for "1984" by George Orwell."""
    book = Books(
        author="George Orwell",
        title="1984",
        year=1949,
        genre="Dystopian Fiction",
        length=328
    )
    session.add(book)
    session.commit()
    return book


# --- Create Book ---

def test_create_book(session):
    """Test creating a new book."""
    Books.create_book("Tolkien", "The Hobbit", 1937, "Fantasy", 310)
    book = session.query(Books).filter_by(title="The Hobbit").first()
    assert book is not None
    assert book.author == "Tolkien"


def test_create_duplicate_book(session, book_mockingbird):
    """Test creating a book with a duplicate author/title/year."""
    with pytest.raises(ValueError, match="already exists"):
        Books.create_book("Harper Lee", "To Kill a Mockingbird", 1960, "Southern Gothic", 281)


@pytest.mark.parametrize("author, title, year, genre, length", [
    ("", "Valid Title", 2000, "Fiction", 150),
    ("Valid Author", "", 2000, "Fiction", 150),
    ("Valid Author", "Valid Title", 1899, "Fiction", 150),
    ("Valid Author", "Valid Title", 2000, "", 150),
    ("Valid Author", "Valid Title", 2000, "Fiction", 0),
])
def test_create_book_invalid_data(author, title, year, genre, length):
    """Test validation errors when creating a book."""
    with pytest.raises(ValueError):
        Books.create_book(author, title, year, genre, length)


# --- Get Book ---

def test_get_book_by_id(book_mockingbird):
    """Test fetching a book by ID."""
    fetched = Books.get_book_by_id(book_mockingbird.id)
    assert fetched.title == "To Kill a Mockingbird"


def test_get_book_by_id_not_found(app):
    """Test error when fetching nonexistent book by ID."""
    with pytest.raises(ValueError, match="not found"):
        Books.get_book_by_id(999)


def test_get_book_by_compound_key(book_1984):
    """Test fetching a book by compound key."""
    book = Books.get_book_by_compound_key("George Orwell", "1984", 1949)
    assert book.genre == "Dystopian Fiction"


def test_get_book_by_compound_key_not_found(app):
    """Test error when fetching nonexistent book by compound key."""
    with pytest.raises(ValueError, match="not found"):
        Books.get_book_by_compound_key("Unknown", "Unknown Book", 2025)


# --- Delete Book ---

def test_delete_book_by_id(session, book_mockingbird):
    """Test deleting a book by ID."""
    Books.delete_book(book_mockingbird.id)
    assert session.get(Books, book_mockingbird.id) is None


def test_delete_book_not_found(app):
    """Test deleting a non-existent book by ID."""
    with pytest.raises(ValueError, match="not found"):
        Books.delete_book(999)


# --- Read Count ---

def test_update_read_count(session, book_1984):
    """Test incrementing read count."""
    assert book_1984.read_count == 0
    book_1984.update_read_count()
    session.refresh(book_1984)
    assert book_1984.read_count == 1


# --- Get All Books ---

def test_get_all_books(session, book_mockingbird, book_1984):
    """Test retrieving all books."""
    books = Books.get_all_books()
    assert len(books) == 2


def test_get_all_books_sorted(session, book_mockingbird, book_1984):
    """Test retrieving books sorted by read count."""
    book_1984.read_count = 5
    book_mockingbird.read_count = 3
    session.commit()
    sorted_books = Books.get_all_books(sort_by_read_count=True)
    assert sorted_books[0]["title"] == "1984"


# --- Random Book ---

def test_get_random_book(session, book_mockingbird, book_1984):
    """Test getting a random book as a dictionary with expected fields."""
    book = Books.get_random_book()

    assert isinstance(book, dict), "Expected a dictionary representing a book"
    assert set(book.keys()) == {"id", "author", "title", "year", "genre", "length", "read_count"}, \
        f"Unexpected keys in book dict: {book.keys()}"
    assert isinstance(book["title"], str) and book["title"], "Book title should be a non-empty string"
    assert isinstance(book["read_count"], int), "Read count should be an integer"


def test_get_random_book_empty(session):
    """Test error when no books exist."""
    Books.query.delete()
    session.commit()
    with pytest.raises(ValueError, match="empty"):
        Books.get_random_book()
