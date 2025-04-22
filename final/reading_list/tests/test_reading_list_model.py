import pytest

from final.readinglist.readinglist.models.reading_list_model import ReadingListModel
from final.readinglist.readinglist.models.book_model import Books


@pytest.fixture()
def reading_list_model():
    """Fixture to provide a new instance of ReadingListModel for each test."""
    return ReadingListModel()

"""Fixtures providing sample books for the tests."""
@pytest.fixture
def book_mockingbird(session):
    """Fixture for To Kill a Mockingbird."""
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
    """Fixture for 1984."""
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


def test_add_book_to_reading_list(reading_list_model, book_mockingbird, mocker):
    """Test adding a book to the reading list."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", return_value=book_mockingbird)
    reading_list_model.add_book_to_reading_list(1)
    assert len(reading_list_model.reading_list) == 1
    assert reading_list_model.reading_list[0] == 1


def test_add_duplicate_book_to_reading_list(reading_list_model, book_mockingbird, mocker):
    """Test error when adding a duplicate book to the reading list by ID."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", side_effect=[book_mockingbird] * 2)
    reading_list_model.add_book_to_reading_list(1)
    with pytest.raises(ValueError, match="Book with ID 1 already exists in the reading_list"):
        reading_list_model.add_book_to_reading_list(1)


def test_remove_book_from_reading_list_by_book_id(reading_list_model, mocker):
    """Test removing a book from the reading list by book_id."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", return_value=book_mockingbird)

    reading_list_model.reading_list = [1,2]

    reading_list_model.remove_book_by_book_id(1)
    assert len(reading_list_model.reading_list) == 1, f"Expected 1 book, but got {len(reading_list_model.reading_list)}"
    assert reading_list_model.reading_list[0] == 2, "Expected book with id 2 to remain"


def test_remove_book_by_selection_number(reading_list_model):
    """Test removing a book from the reading list by selection number."""
    reading_list_model.reading_list = [1,2]
    assert len(reading_list_model.reading_list) == 2

    reading_list_model.remove_book_by_selection_number(1)
    assert len(reading_list_model.reading_list) == 1, f"Expected 1 book, but got {len(reading_list_model.reading_list)}"
    assert reading_list_model.reading_list[0] == 2, "Expected book with id 2 to remain"


def test_clear_reading_list(reading_list_model):
    """Test clearing the entire reading list."""
    reading_list_model.reading_list.append(1)

    reading_list_model.clear_reading_list()
    assert len(reading_list_model.reading_list) == 0, "Reading list should be empty after clearing"


# ##################################################
# # Reading List Management Test Cases
# ##################################################


def test_move_book_to_selection_number(reading_list_model, sample_reading_list, mocker):
    """Test moving a book to a specific selection number in the reading list."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1, 2])

    reading_list_model.move_book_to_selection_number(2, 1)  # Move Book 2 to the first position
    assert reading_list_model.reading_list[0] == 2, "Expected Book 2 to be in the first position"
    assert reading_list_model.reading_list[1] == 1, "Expected Book 1 to be in the second position"


def test_swap_books_in_reading_list(reading_list_model, sample_reading_list, mocker):
    """Test swapping the positions of two books in the reading list."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1, 2])

    reading_list_model.swap_books_in_reading_list(1, 2)  # Swap positions of Book 1 and Book 2
    assert reading_list_model.reading_list[0] == 2, "Expected Book 2 to be in the first position"
    assert reading_list_model.reading_list[1] == 1, "Expected Book 1 to be in the second position"


def test_swap_book_with_itself(reading_list_model, book_mockingbird, mocker):
    """Test swapping the position of a book with itself raises an error."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", side_effect=[book_mockingbird] * 2)
    reading_list_model.reading_list.append(1)

    with pytest.raises(ValueError, match="Cannot swap a book with itself"):
        reading_list_model.swap_books_in_reading_list(1, 1)  # Swap positions of Book 1 with itself


def test_move_book_to_end(reading_list_model, sample_reading_list, mocker):
    """Test moving a book to the end of the reading list."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1, 2])

    reading_list_model.move_book_to_end(1)  # Move Book 1 to the end
    assert reading_list_model.reading_list[1] == 1, "Expected Book 1 to be at the end"


def test_move_book_to_beginning(reading_list_model, sample_reading_list, mocker):
    """Test moving a book to the beginning of the reading list."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1, 2])

    reading_list_model.move_book_to_beginning(2)  # Move Book 2 to the beginning
    assert reading_list_model.reading_list[0] == 2, "Expected Book 2 to be at the beginning"


##################################################
# Book Retrieval Test Cases
##################################################


def test_get_book_by_selection_number(reading_list_model, book_mockingbird, mocker):
    """Test successfully retrieving a book from the reading list by selection number."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", return_value=book_mockingbird)
    reading_list_model.reading_list.append(1)

    retrieved_book = reading_list_model.get_book_by_selection_number(1)
    assert retrieved_book.id == 1
    assert retrieved_book.title == 'Come Together'
    assert retrieved_book.author == 'The Beatles'
    assert retrieved_book.year == 1969
    assert retrieved_book.length == 259
    assert retrieved_book.genre == 'Rock'


def test_get_all_books(reading_list_model, sample_reading_list, mocker):
    """Test successfully retrieving all books from the reading list."""
    mocker.patch("reading_list.models.reading_list_model.ReadingListModel._get_book_from_cache_or_db", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1, 2])

    all_books = reading_list_model.get_all_books()

    assert len(all_books) == 2
    assert all_books[0].id == 1
    assert all_books[1].id == 2


def test_get_book_by_book_id(reading_list_model, book_mockingbird, mocker):
    """Test successfully retrieving a book from the reading list by book ID."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", return_value=book_mockingbird)
    reading_list_model.reading_list.append(1)

    retrieved_book = reading_list_model.get_book_by_book_id(1)

    assert retrieved_book.id == 1
    assert retrieved_book.title == 'Come Together'
    assert retrieved_book.author == 'The Beatles'
    assert retrieved_book.year == 1969
    assert retrieved_book.length == 259
    assert retrieved_book.genre == 'Rock'


def test_get_current_book(reading_list_model, book_mockingbird, mocker):
    """Test successfully retrieving the current book from the reading list."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", return_value=book_mockingbird)

    reading_list_model.reading_list.append(1)

    current_book = reading_list_model.get_current_book()
    assert current_book.id == 1
    assert current_book.title == 'Come Together'
    assert current_book.author == 'The Beatles'
    assert current_book.year == 1969
    assert current_book.length == 259
    assert current_book.genre == 'Rock'


def test_get_reading_list_length(reading_list_model):
    """Test getting the length of the reading list."""
    reading_list_model.reading_list.extend([1, 2])
    assert reading_list_model.get_reading_list_length() == 2, "Expected reading list length to be 2"


def test_get_reading_list_length(reading_list_model, sample_reading_list, mocker):
    """Test getting the total page length of the reading list."""
    mocker.patch("reading_list.models.reading_list_model.ReadingListModel._get_book_from_cache_or_db", side_effect=sample_reading_list)
    reading_list_model.reading_list.extend([1, 2])
    assert reading_list_model.get_reading_list_length() == 609, "Expected reading list page length to be 609 pages"


##################################################
# Utility Function Test Cases
##################################################


def test_check_if_empty_non_empty_reading_list(reading_list_model):
    """Test check_if_empty does not raise error if reading list is not empty."""
    reading_list_model.reading_list.append(1)
    try:
        reading_list_model.check_if_empty()
    except ValueError:
        pytest.fail("check_if_empty raised ValueError unexpectedly on non-empty reading list")


def test_check_if_empty_empty_reading_list(reading_list_model):
    """Test check_if_empty raises error when reading_list is empty."""
    reading_list_model.clear_reading_list()
    with pytest.raises(ValueError, match="Reading list is empty"):
        reading_list_model.check_if_empty()


def test_validate_book_id(reading_list_model, mocker):
    """Test validate_book_id does not raise error for valid book ID."""
    mocker.patch("reading_list.models.reading_list_model.ReadingListModel._get_book_from_cache_or_db", return_value=True)

    reading_list_model.reading_list.append(1)
    try:
        reading_list_model.validate_book_id(1)
    except ValueError:
        pytest.fail("validate_book_id raised ValueError unexpectedly for valid book ID")


def test_validate_book_id_no_check_in_reading_list(reading_list_model, mocker):
    """Test validate_book_id does not raise error for valid book ID when the id isn't in the reading list."""
    mocker.patch("reading_list.models.reading_list_model.ReadingListModel._get_book_from_cache_or_db", return_value=True)
    try:
        reading_list_model.validate_book_id(1, check_in_reading_list=False)
    except ValueError:
        pytest.fail("validate_book_id raised ValueError unexpectedly for valid book ID")


def test_validate_book_id_invalid_id(reading_list_model):
    """Test validate_book_id raises error for invalid book ID."""
    with pytest.raises(ValueError, match="Invalid book id: -1"):
        reading_list_model.validate_book_id(-1)

    with pytest.raises(ValueError, match="Invalid book id: invalid"):
        reading_list_model.validate_book_id("invalid")


def test_validate_book_id_not_in_reading_list(reading_list_model, book_1984, mocker):
    """Test validate_book_id raises error for book ID not in the reading list."""
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", return_value=book_1984)
    reading_list_model.reading_list.append(1)
    with pytest.raises(ValueError, match="Book with id 2 not found in reading_list"):
        reading_list_model.validate_book_id(2)


def test_validate_selection_number(reading_list_model):
    """Test validate_selection_number does not raise error for valid selection number."""
    reading_list_model.reading_list.append(1)
    try:
        reading_list_model.validate_selection_number(1)
    except ValueError:
        pytest.fail("validate_selection_number raised ValueError unexpectedly for valid selection number")

@pytest.mark.parametrize("selection_number, expected_error", [
    (0, "Invalid selection number: 0"),
    (2, "Invalid selection number: 2"),
    ("invalid", "Invalid selection number: invalid"),
])
def test_validate_selection_number_invalid(reading_list_model, selection_number, expected_error):
    """Test validate_selection_number raises error for invalid selection numbers."""
    reading_list_model.reading_list.append(1)

    with pytest.raises(ValueError, match=expected_error):
        reading_list_model.validate_selection_number(selection_number)



##################################################
# Reading Test Cases
##################################################


def test_read_current_book(reading_list_model, sample_reading_list, mocker):
    """Test reading the current book."""
    mock_update_read_count = mocker.patch("reading_list.models.reading_list_model.Books.update_read_count")
    mocker.patch("reading_list.models.reading_list_model.Books.get_book_by_id", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1, 2])

    reading_list_model.read_current_book()

    # Assert that CURRENT_SELECTION_NUMBER has been updated to 2
    assert reading_list_model.current_selection_number == 2, f"Expected selection number to be 2, but got {reading_list_model.current_selection_number}"

    # Assert that update_read_count was called with the id of the first book
    mock_update_read_count.assert_called_once_with()

    # Get the second book from the iterator (which will increment CURRENT_SELECTION_NUMBER back to 1)
    reading_list_model.read_current_book()

    # Assert that CURRENT_SELECTION_NUMBER has been updated back to 1
    assert reading_list_model.current_selection_number == 1, f"Expected selection number to be 1, but got {reading_list_model.current_selection_number}"

    # Assert that update_read_count was called with the id of the second book
    mock_update_read_count.assert_called_with()


def test_rewind_reading_list(reading_list_model):
    """Test rewinding the iterator to the beginning of the reading list."""
    reading_list_model.reading_list.extend([1, 2])
    reading_list_model.current_selection_number = 2

    reading_list_model.rewind_reading_list()
    assert reading_list_model.current_selection_number == 1, "Expected to rewind to the first selection"


def test_go_to_selection_number(reading_list_model):
    """Test moving the iterator to a specific selection number in the reading list."""
    reading_list_model.reading_list.extend([1, 2])

    reading_list_model.go_to_selection_number(2)
    assert reading_list_model.current_selection_number == 2, "Expected to be at selection 2 after moving book"


def test_go_to_random_selection(reading_list_model, mocker):
    """Test that go_to_random_selection sets a valid random selection number."""
    reading_list_model.reading_list.extend([1, 2])

    mocker.patch("reading_list.models.reading_list_model.get_random", return_value=2)

    reading_list_model.go_to_random_selection()
    assert reading_list_model.current_selection_number == 2, "Current selection number should be set to the random value"


def test_read_entire_reading_list(reading_list_model, sample_reading_list, mocker):
    """Test reading the entire reading_list."""
    mock_update_read_count = mocker.patch("reading_list.models.reading_list_model.Books.update_read_count")
    mocker.patch("reading_list.models.reading_list_model.ReadingListModel._get_book_from_cache_or_db", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1,2])

    reading_list_model.read_entire_reading_list()

    # Check that all read counts were updated
    mock_update_read_count.assert_any_call()
    assert mock_update_read_count.call_count == len(reading_list_model.reading_list)

    # Check that the current selection number was updated back to the first book
    assert reading_list_model.current_selection_number == 1, "Expected to loop back to the beginning of the reading list"


def test_read_rest_of_reading_list(reading_list_model, sample_reading_list, mocker):
    """Test reading from the current position to the end of the reading list.

    """
    mock_update_read_count = mocker.patch("reading_list.models.reading_list_model.Books.update_read_count")
    mocker.patch("reading_list.models.reading_list_model.ReadingListModel._get_book_from_cache_or_db", side_effect=sample_reading_list)

    reading_list_model.reading_list.extend([1, 2])
    reading_list_model.current_selection_number = 2

    reading_list_model.read_rest_of_reading_list()

    # Check that read counts were updated for the remaining books
    mock_update_read_count.assert_any_call()
    assert mock_update_read_count.call_count == 1

    assert reading_list_model.current_selection_number == 1, "Expected to loop back to the beginning of the reading list"