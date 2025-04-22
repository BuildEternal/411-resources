import pytest

from final.readinglist.readinglist.models.readinglist_model import ReadingListModel
from final.readinglist.readinglist.models.book_model import Books


@pytest.fixture()
def readinglist_model():
    """Fixture to provide a new instance of ReadingListModel for each test."""
    return ReadingListModel()

"""Fixtures providing sample books for the tests."""
@pytest.fixture
def book_mockingbird(session):
    """Fixture for a book: To Kill a Mockingbird."""
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
    """Fixture for a book: 1984."""
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

@pytest.fixture
def sample_reading_list(book_mockingbird, book_1984):
    """Fixture for a sample reading list."""
    return [book_mockingbird, book_1984]

##################################################
# Add / Remove Book Management Test Cases
##################################################

def test_add_book_to_reading_list(readinglist_model, book_mockingbird, mocker):
    """Test adding a book to the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        return_value=book_mockingbird
    )
    readinglist_model.add_book_to_reading_list(1)
    assert len(readinglist_model.reading_list) == 1
    assert readinglist_model.reading_list[0] == 1


def test_add_duplicate_book_to_reading_list(readinglist_model, book_mockingbird, mocker):
    """Test error when adding a duplicate book to the reading list by ID."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        side_effect=[book_mockingbird, book_mockingbird]
    )
    readinglist_model.add_book_to_reading_list(1)
    with pytest.raises(ValueError, match="Book with ID 1 already exists in the reading list"):
        readinglist_model.add_book_to_reading_list(1)


def test_remove_book_by_book_id(readinglist_model, mocker):
    """Test removing a book from the reading list by book_id."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        return_value=book_mockingbird
    )
    readinglist_model.reading_list = [1, 2]

    readinglist_model.remove_book_by_book_id(1)
    assert len(readinglist_model.reading_list) == 1, \
        f"Expected 1 book, but got {len(readinglist_model.reading_list)}"
    assert readinglist_model.reading_list[0] == 2, "Expected book with id 2 to remain"


def test_remove_book_by_selection_number(readinglist_model):
    """Test removing a book from the reading list by selection number."""
    readinglist_model.reading_list = [1, 2]
    assert len(readinglist_model.reading_list) == 2

    readinglist_model.remove_book_by_selection_number(1)
    assert len(readinglist_model.reading_list) == 1, \
        f"Expected 1 book, but got {len(readinglist_model.reading_list)}"
    assert readinglist_model.reading_list[0] == 2, "Expected book with id 2 to remain"


def test_clear_reading_list(readinglist_model):
    """Test clearing the entire reading list."""
    readinglist_model.reading_list.append(1)

    readinglist_model.clear_reading_list()
    assert len(readinglist_model.reading_list) == 0, "Reading list should be empty after clearing"

##################################################
# Selection Management Test Cases
##################################################

def test_move_book_to_selection_number(readinglist_model, sample_reading_list, mocker):
    """Test moving a book to a specific selection number in the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])

    readinglist_model.move_book_to_selection_number(2, 1)
    assert readinglist_model.reading_list[0] == 2, "Expected book 2 to be first"
    assert readinglist_model.reading_list[1] == 1, "Expected book 1 to be second"


def test_swap_books_in_reading_list(readinglist_model, sample_reading_list, mocker):
    """Test swapping the positions of two books in the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])

    readinglist_model.swap_books_in_reading_list(1, 2)
    assert readinglist_model.reading_list[0] == 2, "Expected book 2 to be first"
    assert readinglist_model.reading_list[1] == 1, "Expected book 1 to be second"


def test_swap_book_with_itself(readinglist_model, book_mockingbird, mocker):
    """Test swapping the position of a book with itself raises an error."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        side_effect=[book_mockingbird, book_mockingbird]
    )
    readinglist_model.reading_list.append(1)

    with pytest.raises(ValueError, match="Cannot swap a book with itself"):
        readinglist_model.swap_books_in_reading_list(1, 1)


def test_move_book_to_end(readinglist_model, sample_reading_list, mocker):
    """Test moving a book to the end of the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])

    readinglist_model.move_book_to_end(1)
    assert readinglist_model.reading_list[1] == 1, "Expected book 1 at the end"


def test_move_book_to_beginning(readinglist_model, sample_reading_list, mocker):
    """Test moving a book to the beginning of the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])

    readinglist_model.move_book_to_beginning(2)
    assert readinglist_model.reading_list[0] == 2, "Expected book 2 at the beginning"

##################################################
# Retrieval Test Cases
##################################################

def test_get_book_by_selection_number(readinglist_model, book_mockingbird, mocker):
    """Test retrieving a book from the reading list by selection number."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        return_value=book_mockingbird
    )
    readinglist_model.reading_list.append(1)

    retrieved_book = readinglist_model.get_book_by_selection_number(1)
    assert retrieved_book.id == 1
    assert retrieved_book.title == 'To Kill a Mockingbird'
    assert retrieved_book.author == 'Harper Lee'
    assert retrieved_book.year == 1960
    assert retrieved_book.length == 281
    assert retrieved_book.genre == 'Southern Gothic'


def test_get_all_books(readinglist_model, sample_reading_list, mocker):
    """Test retrieving all books from the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.ReadingListModel._get_book_from_cache_or_db",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])

    all_books = readinglist_model.get_all_books()

    assert len(all_books) == 2
    assert all_books[0].id == 1
    assert all_books[1].id == 2


def test_get_book_by_book_id(readinglist_model, book_mockingbird, mocker):
    """Test retrieving a book from the reading list by book ID."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        return_value=book_mockingbird
    )
    readinglist_model.reading_list.append(1)

    retrieved_book = readinglist_model.get_book_by_book_id(1)

    assert retrieved_book.id == 1
    assert retrieved_book.title == 'To Kill a Mockingbird'
    assert retrieved_book.author == 'Harper Lee'
    assert retrieved_book.year == 1960
    assert retrieved_book.length == 281
    assert retrieved_book.genre == 'Southern Gothic'


def test_get_current_book(readinglist_model, book_mockingbird, mocker):
    """Test retrieving the current book from the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        return_value=book_mockingbird
    )

    readinglist_model.reading_list.append(1)

    current_book = readinglist_model.get_current_book()
    assert current_book.id == 1
    assert current_book.title == 'To Kill a Mockingbird'
    assert current_book.author == 'Harper Lee'
    assert current_book.year == 1960
    assert current_book.length == 281
    assert current_book.genre == 'Southern Gothic'


def test_reading_list_length(readinglist_model):
    """Test getting the length of the reading list."""
    readinglist_model.reading_list.extend([1, 2])
    assert readinglist_model.get_reading_list_length() == 2, \
        "Expected reading list length to be 2"


def test_reading_list_page_count(readinglist_model, sample_reading_list, mocker):
    """Test getting the total pages of the reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.ReadingListModel._get_book_from_cache_or_db",
        side_effect=sample_reading_list
    )
    readinglist_model.reading_list.extend([1, 2])
    assert readinglist_model.get_reading_list_page_count() == 609, \
        "Expected total page count to be 609"

##################################################
# Utility Function Test Cases
##################################################

def test_check_if_empty_non_empty_reading_list(readinglist_model):
    """Test check_if_empty does not raise error if reading list is not empty."""
    readinglist_model.reading_list.append(1)
    try:
        readinglist_model.check_if_empty()
    except ValueError:
        pytest.fail("check_if_empty raised ValueError unexpectedly on non-empty reading list")


def test_check_if_empty_empty_reading_list(readinglist_model):
    """Test check_if_empty raises error when reading list is empty."""
    readinglist_model.clear_reading_list()
    with pytest.raises(ValueError, match="Reading list is empty"):
        readinglist_model.check_if_empty()


def test_validate_book_id(readinglist_model, mocker):
    """Test validate_book_id does not raise error for valid book ID."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.ReadingListModel._get_book_from_cache_or_db",
        return_value=True
    )

    readinglist_model.reading_list.append(1)
    try:
        readinglist_model.validate_book_id(1)
    except ValueError:
        pytest.fail("validate_book_id raised ValueError unexpectedly for valid book ID")


def test_validate_book_id_no_check_in_reading_list(readinglist_model, mocker):
    """Test validate_book_id does not raise error when check_in_list=False."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.ReadingListModel._get_book_from_cache_or_db",
        return_value=True
    )
    try:
        readinglist_model.validate_book_id(1, check_in_list=False)
    except ValueError:
        pytest.fail("validate_book_id raised ValueError unexpectedly for valid book ID")


def test_validate_book_id_invalid(readinglist_model):
    """Test validate_book_id raises error for invalid book ID."""
    with pytest.raises(ValueError, match="Invalid book id: -1"):
        readinglist_model.validate_book_id(-1)

    with pytest.raises(ValueError, match="Invalid book id: invalid"):
        readinglist_model.validate_book_id("invalid")


def test_validate_book_id_not_in_reading_list(readinglist_model, book_1984, mocker):
    """Test validate_book_id raises error for book ID not in reading list."""
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        return_value=book_1984
    )
    readinglist_model.reading_list.append(1)
    with pytest.raises(ValueError, match="Book with id 2 not found in reading list"):
        readinglist_model.validate_book_id(2)


def test_validate_selection_number(readinglist_model):
    """Test validate_selection_number does not raise error for valid selection number."""
    readinglist_model.reading_list.append(1)
    try:
        readinglist_model.validate_selection_number(1)
    except ValueError:
        pytest.fail("validate_selection_number raised ValueError unexpectedly for valid selection number")

@pytest.mark.parametrize("selection_number, expected_error", [
    (0, "Invalid selection number: 0"),
    (2, "Invalid selection number: 2"),
    ("invalid", "Invalid selection number: invalid"),
])
def test_validate_selection_number_invalid(readinglist_model, selection_number, expected_error):
    """Test validate_selection_number raises error for invalid selection numbers."""
    readinglist_model.reading_list.append(1)

    with pytest.raises(ValueError, match=expected_error):
        readinglist_model.validate_selection_number(selection_number)

##################################################
# Read Test Cases
##################################################

def test_read_current_book(readinglist_model, sample_reading_list, mocker):
    """Test reading the current book."""
    mock_update_read_count = mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.update_read_count"
    )
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.get_book_by_id",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])

    readinglist_model.read_current_book()

    # CURRENT_SELECTION_NUMBER updated to 2
    assert readinglist_model.current_selection_number == 2, \
        f"Expected selection number to be 2, but got {readinglist_model.current_selection_number}"

    mock_update_read_count.assert_called_once_with()

    readinglist_model.read_current_book()
    assert readinglist_model.current_selection_number == 1, \
        f"Expected selection number to be 1, but got {readinglist_model.current_selection_number}"
    mock_update_read_count.assert_called_with()


def test_rewind_reading_list(readinglist_model):
    """Test rewinding the iterator to the beginning of the reading list."""
    readinglist_model.reading_list.extend([1, 2])
    readinglist_model.current_selection_number = 2

    readinglist_model.rewind_reading_list()
    assert readinglist_model.current_selection_number == 1, "Expected to rewind to first selection"


def test_go_to_selection_number(readinglist_model):
    """Test moving the iterator to a specific selection number."""
    readinglist_model.reading_list.extend([1, 2])

    readinglist_model.go_to_selection_number(2)
    assert readinglist_model.current_selection_number == 2, "Expected to be at selection 2"


def test_go_to_random_selection(readinglist_model, mocker):
    """Test that go_to_random_selection sets a valid random selection number."""
    readinglist_model.reading_list.extend([1, 2])

    mocker.patch("final.readinglist.readinglist.models.readinglist_model.get_random", return_value=2)

    readinglist_model.go_to_random_selection()
    assert readinglist_model.current_selection_number == 2, "Selection number should be random value"


def test_read_entire_reading_list(readinglist_model, sample_reading_list, mocker):
    """Test reading the entire reading list."""
    mock_update_read_count = mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.update_read_count"
    )
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.ReadingListModel._get_book_from_cache_or_db",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])

    readinglist_model.read_entire_reading_list()

    mock_update_read_count.assert_any_call()
    assert mock_update_read_count.call_count == len(readinglist_model.reading_list)
    assert readinglist_model.current_selection_number == 1, \
        "Expected to loop back to beginning of reading list"


def test_read_rest_of_reading_list(readinglist_model, sample_reading_list, mocker):
    """Test reading from the current position to the end of the reading list."""
    mock_update_read_count = mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.Books.update_read_count"
    )
    mocker.patch(
        "final.readinglist.readinglist.models.readinglist_model.ReadingListModel._get_book_from_cache_or_db",
        side_effect=sample_reading_list
    )

    readinglist_model.reading_list.extend([1, 2])
    readinglist_model.current_selection_number = 2

    readinglist_model.read_rest_of_reading_list()

    mock_update_read_count.assert_any_call()
    assert mock_update_read_count.call_count == 1
    assert readinglist_model.current_selection_number == 1, \
        "Expected to loop back to beginning of reading list"
