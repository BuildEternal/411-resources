from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import ProductionConfig

from readinglist.db import db
from readinglist.models.book_model import Books
from readinglist.models.readinglist_model import ReadingListModel
from readinglist.models.user_model import Users
from readinglist.utils.logger import configure_logger


load_dotenv()


def create_app(config_class=ProductionConfig) -> Flask:
    """Create a Flask application with the specified configuration.

    Args:
        config_class (Config): The configuration class to use.

    Returns:
        Flask app: The configured Flask application.

    """
    app = Flask(__name__)
    configure_logger(app.logger)

    app.config.from_object(config_class)

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.filter_by(username=user_id).first()

    @login_manager.unauthorized_handler
    def unauthorized():
        return make_response(jsonify({
            "status": "error",
            "message": "Authentication required"
        }), 401)

    reading_list_model = ReadingListModel()

    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.

        """
        app.logger.info("Health check endpoint hit")
        return make_response(jsonify({
            'status': 'success',
            'message': 'Service is running'
        }), 200)

    ##########################################################
    #
    # User Management
    #
    #########################################################

    @app.route('/api/create-user', methods=['PUT'])
    def create_user() -> Response:
        """Register a new user account.

        Expected JSON Input:
            - username (str): The desired username.
            - password (str): The desired password.

        Returns:
            JSON response indicating the success of the user creation.

        Raises:
            400 error if the username or password is missing.
            500 error if there is an issue creating the user in the database.
        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            Users.create_user(username, password)
            return make_response(jsonify({
                "status": "success",
                "message": f"User '{username}' created successfully"
            }), 201)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"User creation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while creating user",
                "details": str(e)
            }), 500)

    @app.route('/api/login', methods=['POST'])
    def login() -> Response:
        """Authenticate a user and log them in.

        Expected JSON Input:
            - username (str): The username of the user.
            - password (str): The password of the user.

        Returns:
            JSON response indicating the success of the login attempt.

        Raises:
            401 error if the username or password is incorrect.
        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            if Users.check_password(username, password):
                user = Users.query.filter_by(username=username).first()
                login_user(user)
                return make_response(jsonify({
                    "status": "success",
                    "message": f"User '{username}' logged in successfully"
                }), 200)
            else:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid username or password"
                }), 401)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 401)
        except Exception as e:
            app.logger.error(f"Login failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred during login",
                "details": str(e)
            }), 500)

    @app.route('/api/logout', methods=['POST'])
    @login_required
    def logout() -> Response:
        """Log out the current user.

        Returns:
            JSON response indicating the success of the logout operation.

        """
        logout_user()
        return make_response(jsonify({
            "status": "success",
            "message": "User logged out successfully"
        }), 200)

    @app.route('/api/change-password', methods=['POST'])
    @login_required
    def change_password() -> Response:
        """Change the password for the current user.

        Expected JSON Input:
            - new_password (str): The new password to set.

        Returns:
            JSON response indicating the success of the password change.

        Raises:
            400 error if the new password is not provided.
            500 error if there is an issue updating the password in the database.
        """
        try:
            data = request.get_json()
            new_password = data.get("new_password")

            if not new_password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "New password is required"
                }), 400)

            username = current_user.username
            Users.update_password(username, new_password)
            return make_response(jsonify({
                "status": "success",
                "message": "Password changed successfully"
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Password change failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while changing password",
                "details": str(e)
            }), 500)

    @app.route('/api/reset-users', methods=['DELETE'])
    def reset_users() -> Response:
        """Recreate the users table to delete all users.

        Returns:
            JSON response indicating the success of recreating the Users table.

        Raises:
            500 error if there is an issue recreating the Users table.
        """
        try:
            app.logger.info("Received request to recreate Users table")
            with app.app_context():
                Users.__table__.drop(db.engine)
                Users.__table__.create(db.engine)
            app.logger.info("Users table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Users table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Users table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)

    ##########################################################
    #
    # Books
    #
    ##########################################################

    @app.route('/api/reset-books', methods=['DELETE'])
    def reset_books() -> Response:
        """Recreate the books table to delete books.

        Returns:
            JSON response indicating the success of recreating the Books table.

        Raises:
            500 error if there is an issue recreating the Books table.
        """
        try:
            app.logger.info("Received request to recreate Books table")
            with app.app_context():
                Books.__table__.drop(db.engine)
                Books.__table__.create(db.engine)
            app.logger.info("Books table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Books table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Books table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)


    @app.route('/api/create-book', methods=['POST'])
    @login_required
    def add_book() -> Response:
        """Route to add a new book to the catalog.

        Expected JSON Input:
            - author (str): The author's name.
            - title (str): The book title.
            - year (int): The year the book was released.
            - genre (str): The genre of the book.
            - length (int): The length of the book in pages.

        Returns:
            JSON response indicating the success of the book addition.

        Raises:
            400 error if input validation fails.
            500 error if there is an issue adding the book to the reading list.

        """
        app.logger.info("Received request to add a new book")

        try:
            data = request.get_json()

            required_fields = ["author", "title", "year", "genre", "length"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            author = data["author"]
            title = data["title"]
            year = data["year"]
            genre = data["genre"]
            length = data["length"]

            if (
                not isinstance(author, str)
                or not isinstance(title, str)
                or not isinstance(year, int)
                or not isinstance(genre, str)
                or not isinstance(length, int)
            ):
                app.logger.warning("Invalid input data types")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid input types: author/title/genre should be strings, year and length should be integers"
                }), 400)

            app.logger.info(f"Adding book: {author} - {title} ({year}), Genre: {genre}, Length: {length} pages")
            Books.create_book(author=author, title=title, year=year, genre=genre, length=length)

            app.logger.info(f"Book added successfully: {author} - {title}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Book '{title}' by {author} added successfully"
            }), 201)

        except Exception as e:
            app.logger.error(f"Failed to add book: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while adding the book",
                "details": str(e)
            }), 500)


    @app.route('/api/delete-book/<int:book_id>', methods=['DELETE'])
    @login_required
    def delete_book(book_id: int) -> Response:
        """Route to delete a book by ID.

        Path Parameter:
            - book_id (int): The ID of the book to delete.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the book does not exist.
            500 error if there is an issue removing the book from the database.

        """
        try:
            app.logger.info(f"Received request to delete book with ID {book_id}")

            # Check if the book exists before attempting to delete
            book = Books.get_book_by_id(book_id)
            if not book:
                app.logger.warning(f"Book with ID {book_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Book with ID {book_id} not found"
                }), 400)

            Books.delete_book(book_id)
            app.logger.info(f"Successfully deleted book with ID {book_id}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Book with ID {book_id} deleted successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to delete book: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting the book",
                "details": str(e)
            }), 500)


    @app.route('/api/get-all-books-from-catalog', methods=['GET'])
    @login_required
    def get_all_books() -> Response:
        """Route to retrieve all books in the catalog (non-deleted), with an option to sort by read count.

        Query Parameter:
            - sort_by_read_count (bool, optional): If true, sort books by read count.

        Returns:
            JSON response containing the list of books.

        Raises:
            500 error if there is an issue retrieving books from the catalog.

        """
        try:
            # Extract query parameter for sorting by read count
            sort_by_read_count = request.args.get('sort_by_read_count', 'false').lower() == 'true'

            app.logger.info(f"Received request to retrieve all books from catalog (sort_by_read_count={sort_by_read_count})")

            books = Books.get_all_books(sort_by_read_count=sort_by_read_count)

            app.logger.info(f"Successfully retrieved {len(books)} books from the catalog")

            return make_response(jsonify({
                "status": "success",
                "message": "Books retrieved successfully",
                "books": books
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve books: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving books",
                "details": str(e)
            }), 500)


    @app.route('/api/get-book-from-catalog-by-id/<int:book_id>', methods=['GET'])
    @login_required
    def get_book_by_id(book_id: int) -> Response:
        """Route to retrieve a book by its ID.

        Path Parameter:
            - book_id (int): The ID of the book.

        Returns:
            JSON response containing the book details.

        Raises:
            400 error if the book does not exist.
            500 error if there is an issue retrieving the book.

        """
        try:
            app.logger.info(f"Received request to retrieve book with ID {book_id}")

            book = Books.get_book_by_id(book_id)
            if not book:
                app.logger.warning(f"Book with ID {book_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Book with ID {book_id} not found"
                }), 400)

            app.logger.info(f"Successfully retrieved book: {book.title} by {book.author} (ID {book_id})")

            return make_response(jsonify({
                "status": "success",
                "message": "Book retrieved successfully",
                "book": book
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve book by ID: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the book",
                "details": str(e)
            }), 500)


    @app.route('/api/get-book-from-catalog-by-compound-key', methods=['GET'])
    @login_required
    def get_book_by_compound_key() -> Response:
        """Route to retrieve a book by its compound key (author, title, year).

        Query Parameters:
            - author (str): The author's name.
            - title (str): The book title.
            - year (int): The year the book was released.

        Returns:
            JSON response containing the book details.

        Raises:
            400 error if required query parameters are missing or invalid.
            500 error if there is an issue retrieving the book.

        """
        try:
            author = request.args.get('author')
            title = request.args.get('title')
            year = request.args.get('year')

            if not author or not title or not year:
                app.logger.warning("Missing required query parameters: author, title, year")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Missing required query parameters: author, title, year"
                }), 400)

            try:
                year = int(year)
            except ValueError:
                app.logger.warning(f"Invalid year format: {year}. Year must be an integer.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Year must be an integer"
                }), 400)

            app.logger.info(f"Received request to retrieve book by compound key: {author}, {title}, {year}")

            book = Books.get_book_by_compound_key(author, title, year)
            if not book:
                app.logger.warning(f"Book not found: {author} - {title} ({year})")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Book not found: {author} - {title} ({year})"
                }), 400)

            app.logger.info(f"Successfully retrieved book: {book.title} by {book.author} ({year})")

            return make_response(jsonify({
                "status": "success",
                "message": "Book retrieved successfully",
                "book": book
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve book by compound key: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the book",
                "details": str(e)
            }), 500)


    @app.route('/api/get-random-book', methods=['GET'])
    @login_required
    def get_random_book() -> Response:
        """Route to retrieve a random book from the catalog.

        Returns:
            JSON response containing the details of a random book.

        Raises:
            400 error if no books exist in the catalog.
            500 error if there is an issue retrieving the book

        """
        try:
            app.logger.info("Received request to retrieve a random book from the catalog")

            book = Books.get_random_book()
            if not book:
                app.logger.warning("No books found in the catalog.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "No books available in the catalog"
                }), 400)

            app.logger.info(f"Successfully retrieved random book: {book.title} by {book.author}")

            return make_response(jsonify({
                "status": "success",
                "message": "Random book retrieved successfully",
                "book": book
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve random book: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving a random book",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # Reading List Add / Remove
    #
    ############################################################


    @app.route('/api/add-book-to-reading-list', methods=['POST'])
    @login_required
    def add_book_to_reading_list() -> Response:
        """Route to add a book to the reading list by compound key (author, title, year).

        Expected JSON Input:
            - author (str): The author's name.
            - title (str): The book title.
            - year (int): The year the book was released.

        Returns:
            JSON response indicating success of the addition.

        Raises:
            400 error if required fields are missing or the book does not exist.
            500 error if there is an issue adding the book to the reading list.

        """
        try:
            app.logger.info("Received request to add book to reading list")

            data = request.get_json()
            required_fields = ["author", "title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            author = data["author"]
            title = data["title"]

            try:
                year = int(data["year"])
            except ValueError:
                app.logger.warning(f"Invalid year format: {data['year']}")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Year must be a valid integer"
                }), 400)

            app.logger.info(f"Looking up book: {author} - {title} ({year})")
            book = Books.get_book_by_compound_key(author, title, year)

            if not book:
                app.logger.warning(f"Book not found: {author} - {title} ({year})")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Book '{title}' by {author} ({year}) not found in catalog"
                }), 400)

            reading_list_model.add_book_to_reading_list(book)
            app.logger.info(f"Successfully added book to reading list: {author} - {title} ({year})")

            return make_response(jsonify({
                "status": "success",
                "message": f"Book '{title}' by {author} ({year}) added to reading list"
            }), 201)

        except Exception as e:
            app.logger.error(f"Failed to add book to reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while adding the book to the reading list",
                "details": str(e)
            }), 500)


    @app.route('/api/remove-book-from-reading-list', methods=['DELETE'])
    @login_required
    def remove_book_by_book_id() -> Response:
        """Route to remove a book from the reading list by compound key (author, title, year).

        Expected JSON Input:
            - author (str): The author's name.
            - title (str): The book title.
            - year (int): The year the book was released.

        Returns:
            JSON response indicating success of the removal.

        Raises:
            400 error if required fields are missing or the book does not exist in the reading list.
            500 error if there is an issue removing the book.

        """
        try:
            app.logger.info("Received request to remove book from reading list")

            data = request.get_json()
            required_fields = ["author", "title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            author = data["author"]
            title = data["title"]

            try:
                year = int(data["year"])
            except ValueError:
                app.logger.warning(f"Invalid year format: {data['year']}")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Year must be a valid integer"
                }), 400)

            app.logger.info(f"Looking up book to remove: {author} - {title} ({year})")
            book = Books.get_book_by_compound_key(author, title, year)

            if not book:
                app.logger.warning(f"Book not found in catalog: {author} - {title} ({year})")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Book '{title}' by {author} ({year}) not found in catalog"
                }), 400)

            reading_list_model.remove_book_by_book_id(book.id)
            app.logger.info(f"Successfully removed book from reading list: {author} - {title} ({year})")

            return make_response(jsonify({
                "status": "success",
                "message": f"Book '{title}' by {author} ({year}) removed from reading list"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to remove book from reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while removing the book from the reading list",
                "details": str(e)
            }), 500)


    @app.route('/api/remove-book-from-reading-list-by-selection-number/<int:selection_number>', methods=['DELETE'])
    @login_required
    def remove_book_by_selection_number(selection_number: int) -> Response:
        """Route to remove a book from the reading list by selection number.

        Path Parameter:
            - selection_number (int): The selection number of the book to remove.

        Returns:
            JSON response indicating success of the removal.

        Raises:
            404 error if the selection number does not exist.
            500 error if there is an issue removing the book.

        """
        try:
            app.logger.info(f"Received request to remove book at selection number {selection_number} from reading list")

            reading_list_model.remove_book_by_selection_number(selection_number)

            app.logger.info(f"Successfully removed book at selection number {selection_number} from reading list")
            return make_response(jsonify({
                "status": "success",
                "message": f"Book at selection number {selection_number} removed from reading list"
            }), 200)

        except ValueError as e:
            app.logger.warning(f"Selection number {selection_number} not found in reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": f"Selection number {selection_number} not found in reading list"
            }), 404)

        except Exception as e:
            app.logger.error(f"Failed to remove book at selection number {selection_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while removing the book from the reading list",
                "details": str(e)
            }), 500)


    @app.route('/api/clear-reading-list', methods=['POST'])
    @login_required
    def clear_reading_list() -> Response:
        """Route to clear all books from the reading list.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            500 error if there is an issue clearing the reading list.

        """
        try:
            app.logger.info("Received request to clear the reading list")

            reading_list_model.clear_reading_list()

            app.logger.info("Successfully cleared the reading list")
            return make_response(jsonify({
                "status": "success",
                "message": "Reading List cleared"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to clear reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while clearing the reading list",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # Read Reading List
    #
    ############################################################


    @app.route('/api/read-current-book', methods=['POST'])
    @login_required
    def read_current_book() -> Response:
        """Route to read the current book in the reading list.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            404 error if there is no current book.
            500 error if there is an issue reading the current book.

        """
        try:
            app.logger.info("Received request to read the current book")

            current_book = reading_list_model.get_current_book()
            if not current_book:
                app.logger.warning("No current book found in the reading list")
                return make_response(jsonify({
                    "status": "error",
                    "message": "No current book found in the reading list"
                }), 404)

            reading_list_model.read_current_book()
            app.logger.info(f"Now reading: {current_book.author} - {current_book.title} ({current_book.year})")

            return make_response(jsonify({
                "status": "success",
                "message": "Now reading current book",
                "book": {
                    "id": current_book.id,
                    "author": current_book.author,
                    "title": current_book.title,
                    "year": current_book.year,
                    "genre": current_book.genre,
                    "length": current_book.length
                }
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to read current book: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while reading the current book",
                "details": str(e)
            }), 500)


    @app.route('/api/read-entire-reading-list', methods=['POST'])
    @login_required
    def read_entire_reading_list() -> Response:
        """Route to read all books in the reading list.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the reading list is empty.
            500 error if there is an issue reading the reading list.

        """
        try:
            app.logger.info("Received request to read the entire reading list")

            if reading_list_model.check_if_empty():
                app.logger.warning("Cannot read reading list: No books available")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot read reading list: No books available"
                }), 400)

            reading_list_model.read_entire_reading_list()
            app.logger.info("Reading entire reading list")

            return make_response(jsonify({
                "status": "success",
                "message": "Reading entire reading list"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to read entire reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while reading the reading list",
                "details": str(e)
            }), 500)


    @app.route('/api/read-rest-of-reading-list', methods=['POST'])
    @login_required
    def read_rest_of_reading_list() -> Response:
        """Route to read the rest of the reading list from the current selection.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the reading list is empty or if no current book is reading.
            500 error if there is an issue reading the rest of the reading list.

        """
        try:
            app.logger.info("Received request to read the rest of the reading list")

            if reading_list_model.check_if_empty():
                app.logger.warning("Cannot read rest of reading list: No books available")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot read rest of reading list: No books available"
                }), 400)

            if not reading_list_model.get_current_book():
                app.logger.warning("No current book reading. Cannot continue reading list.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "No current book reading. Cannot continue reading list."
                }), 400)

            reading_list_model.read_rest_of_reading_list()
            app.logger.info("Reading rest of the reading list")

            return make_response(jsonify({
                "status": "success",
                "message": "Reading rest of the reading list"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to read rest of the reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while reading the rest of the reading list",
                "details": str(e)
            }), 500)


    @app.route('/api/rewind-reading-list', methods=['POST'])
    @login_required
    def rewind_reading_list() -> Response:
        """Route to rewind the reading list to the first book.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the reading list is empty.
            500 error if there is an issue rewinding the reading list.

        """
        try:
            app.logger.info("Received request to rewind the reading list")

            if reading_list_model.check_if_empty():
                app.logger.warning("Cannot rewind: No books in reading list")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot rewind: No books in reading list"
                }), 400)

            reading_list_model.rewind_reading_list()
            app.logger.info("Reading List successfully rewound to the first book")

            return make_response(jsonify({
                "status": "success",
                "message": "Reading List rewound to the first book"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to rewind reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while rewinding the reading list",
                "details": str(e)
            }), 500)


    @app.route('/api/go-to-selection-number/<int:selection_number>', methods=['POST'])
    @login_required
    def go_to_selection_number(selection_number: int) -> Response:
        """Route to set the reading list to start reading from a specific selection number.

        Path Parameter:
            - selection_number (int): The selection number to set as the current book.

        Returns:
            JSON response indicating success or an error message.

        Raises:
            400 error if the selection number is invalid.
            500 error if there is an issue updating the selection number.
        """
        try:
            app.logger.info(f"Received request to go to selection number {selection_number}")

            if not reading_list_model.is_valid_selection_number(selection_number):
                app.logger.warning(f"Invalid selection number: {selection_number}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Invalid selection number: {selection_number}. Please provide a valid selection number."
                }), 400)

            reading_list_model.go_to_selection_number(selection_number)
            app.logger.info(f"Reading List set to selection number {selection_number}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Now reading from selection number {selection_number}"
            }), 200)

        except ValueError as e:
            app.logger.warning(f"Failed to set selection number {selection_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)

        except Exception as e:
            app.logger.error(f"Internal error while going to selection number {selection_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while changing the selection number",
                "details": str(e)
            }), 500)


    @app.route('/api/go-to-random-selection', methods=['POST'])
    @login_required
    def go_to_random_selection() -> Response:
        """Route to set the reading list to start reading from a random selection number.

        Returns:
            JSON response indicating success or an error message.

        Raises:
            400 error if the reading list is empty.
            500 error if there is an issue selecting a random selection.

        """
        try:
            app.logger.info("Received request to go to a random selection")

            if reading_list_model.get_reading_list_length() == 0:
                app.logger.warning("Attempted to go to a random selection but the reading list is empty")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot select a random selection. The reading list is empty."
                }), 400)

            reading_list_model.go_to_random_selection()
            app.logger.info(f"Reading List set to random selection number {reading_list_model.current_selection_number}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Now reading from random selection number {reading_list_model.current_selection_number}"
            }), 200)

        except Exception as e:
            app.logger.error(f"Internal error while selecting a random selection: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while selecting a random selection",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # View Reading List
    #
    ############################################################


    @app.route('/api/get-all-books-from-reading-list', methods=['GET'])
    @login_required
    def get_all_books_from_reading_list() -> Response:
        """Retrieve all books in the reading list.

        Returns:
            JSON response containing the list of books.

        Raises:
            500 error if there is an issue retrieving the reading list.

        """
        try:
            app.logger.info("Received request to retrieve all books from the reading list.")

            books = reading_list_model.get_all_books()

            app.logger.info(f"Successfully retrieved {len(books)} books from the reading list.")
            return make_response(jsonify({
                "status": "success",
                "books": books
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve books from reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the reading list",
                "details": str(e)
            }), 500)


    @app.route('/api/get-book-from-reading-list-by-selection-number/<int:selection_number>', methods=['GET'])
    @login_required
    def get_book_by_selection_number(selection_number: int) -> Response:
        """Retrieve a book from the reading list by selection number.

        Path Parameter:
            - selection_number (int): The selection number of the book.

        Returns:
            JSON response containing book details.

        Raises:
            404 error if the selection number is not found.
            500 error if there is an issue retrieving the book.

        """
        try:
            app.logger.info(f"Received request to retrieve book at selection number {selection_number}.")

            book = reading_list_model.get_book_by_selection_number(selection_number)

            app.logger.info(f"Successfully retrieved book: {book.author} - {book.title} (Selection {selection_number}).")
            return make_response(jsonify({
                "status": "success",
                "book": book
            }), 200)

        except ValueError as e:
            app.logger.warning(f"Selection number {selection_number} not found: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 404)

        except Exception as e:
            app.logger.error(f"Failed to retrieve book by selection number {selection_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the book",
                "details": str(e)
            }), 500)


    @app.route('/api/get-current-book', methods=['GET'])
    @login_required
    def get_current_book() -> Response:
        """Retrieve the current book being readed.

        Returns:
            JSON response containing current book details.

        Raises:
            500 error if there is an issue retrieving the current book.

        """
        try:
            app.logger.info("Received request to retrieve the current book.")

            current_book = reading_list_model.get_current_book()

            app.logger.info(f"Successfully retrieved current book: {current_book.author} - {current_book.title}.")
            return make_response(jsonify({
                "status": "success",
                "current_book": current_book
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve current book: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the current book",
                "details": str(e)
            }), 500)


    @app.route('/api/get-reading-list-length', methods=['GET'])
    @login_required
    def get_reading_list_length() -> Response:
        """Retrieve the length (number of books) and total length in pages of the reading list.

        Returns:
            JSON response containing the reading list length and total length in pages.

        Raises:
            500 error if there is an issue retrieving reading list information.

        """
        try:
            app.logger.info("Received request to retrieve reading list length in books and length in pages.")

            reading_list_length = reading_list_model.get_reading_list_length()
            reading_list_page_length = reading_list_model.get_reading_list_length()

            app.logger.info(f"Reading List contains {reading_list_length} books with a total length of {reading_list_page_length} pages.")
            return make_response(jsonify({
                "status": "success",
                "reading_list_length": reading_list_length,
                "reading_list_length": reading_list_page_length
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve reading list length and total page length: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving reading list details",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # Arrange Reading List
    #
    ############################################################


    @app.route('/api/move-book-to-beginning', methods=['POST'])
    @login_required
    def move_book_to_beginning() -> Response:
        """Move a book to the beginning of the reading list.

        Expected JSON Input:
            - author (str): The author of the book.
            - title (str): The title of the book.
            - year (int): The year the book was released.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 error if an error occurs while updating the reading list.

        """
        try:
            data = request.get_json()

            required_fields = ["author", "title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            author, title, year = data["author"], data["title"], data["year"]
            app.logger.info(f"Received request to move book to beginning: {author} - {title} ({year})")

            book = Books.get_book_by_compound_key(author, title, year)
            reading_list_model.move_book_to_beginning(book.id)

            app.logger.info(f"Successfully moved book to beginning: {author} - {title} ({year})")
            return make_response(jsonify({
                "status": "success",
                "message": f"Book '{title}' by {author} moved to beginning"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to move book to beginning: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while moving the book",
                "details": str(e)
            }), 500)


    @app.route('/api/move-book-to-end', methods=['POST'])
    @login_required
    def move_book_to_end() -> Response:
        """Move a book to the end of the reading list.

        Expected JSON Input:
            - author (str): The author of the book.
            - title (str): The title of the book.
            - year (int): The year the book was released.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 if an error occurs while updating the reading list.

        """
        try:
            data = request.get_json()

            required_fields = ["author", "title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            author, title, year = data["author"], data["title"], data["year"]
            app.logger.info(f"Received request to move book to end: {author} - {title} ({year})")

            book = Books.get_book_by_compound_key(author, title, year)
            reading_list_model.move_book_to_end(book.id)

            app.logger.info(f"Successfully moved book to end: {author} - {title} ({year})")
            return make_response(jsonify({
                "status": "success",
                "message": f"Book '{title}' by {author} moved to end"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to move book to end: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while moving the book",
                "details": str(e)
            }), 500)


    @app.route('/api/move-book-to-selection-number', methods=['POST'])
    @login_required
    def move_book_to_selection_number() -> Response:
        """Move a book to a specific selection number in the reading list.

        Expected JSON Input:
            - author (str): The author of the book.
            - title (str): The title of the book.
            - year (int): The year the book was released.
            - selection_number (int): The new selection number to move the book to.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 error if an error occurs while updating the reading list.
        """
        try:
            data = request.get_json()

            required_fields = ["author", "title", "year", "selection_number"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            author, title, year, selection_number = data["author"], data["title"], data["year"], data["selection_number"]
            app.logger.info(f"Received request to move book to selection number {selection_number}: {author} - {title} ({year})")

            book = Books.get_book_by_compound_key(author, title, year)
            reading_list_model.move_book_to_selection_number(book.id, selection_number)

            app.logger.info(f"Successfully moved book to selection {selection_number}: {author} - {title} ({year})")
            return make_response(jsonify({
                "status": "success",
                "message": f"Book '{title}' by {author} moved to selection {selection_number}"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to move book to selection number: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while moving the book",
                "details": str(e)
            }), 500)


    @app.route('/api/swap-books-in-reading-list', methods=['POST'])
    @login_required
    def swap_books_in_reading_list() -> Response:
        """Swap two books in the reading list by their selection numbers.

        Expected JSON Input:
            - selection_number_1 (int): The selection number of the first book.
            - selection_number_2 (int): The selection number of the second book.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 error if an error occurs while swapping books in the reading list.
        """
        try:
            data = request.get_json()

            required_fields = ["selection_number_1", "selection_number_2"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            selection_number_1, selection_number_2 = data["selection_number_1"], data["selection_number_2"]
            app.logger.info(f"Received request to swap books at selection numbers {selection_number_1} and {selection_number_2}")

            book_1 = reading_list_model.get_book_by_selection_number(selection_number_1)
            book_2 = reading_list_model.get_book_by_selection_number(selection_number_2)
            reading_list_model.swap_books_in_reading_list(book_1.id, book_2.id)

            app.logger.info(f"Successfully swapped books: {book_1.author} - {book_1.title} <-> {book_2.author} - {book_2.title}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Swapped books: {book_1.author} - {book_1.title} <-> {book_2.author} - {book_2.title}"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to swap books in reading list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while swapping books",
                "details": str(e)
            }), 500)



    ############################################################
    #
    # Leaderboard / Stats
    #
    ############################################################


    @app.route('/api/book-leaderboard', methods=['GET'])
    def get_book_leaderboard() -> Response:
        """
        Route to retrieve a leaderboard of books sorted by read count.

        Returns:
            JSON response with a sorted leaderboard of books.

        Raises:
            500 error if there is an issue generating the leaderboard.

        """
        try:
            app.logger.info("Received request to generate book leaderboard")

            leaderboard_data = Books.get_all_books(sort_by_read_count=True)

            app.logger.info(f"Successfully generated book leaderboard with {len(leaderboard_data)} entries")
            return make_response(jsonify({
                "status": "success",
                "leaderboard": leaderboard_data
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to generate book leaderboard: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while generating the leaderboard",
                "details": str(e)
            }), 500)

    return app

if __name__ == '__main__':
    app = create_app()
    app.logger.info("Starting Flask app...")
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        app.logger.error(f"Flask app encountered an error: {e}")
    finally:
        app.logger.info("Flask app has stopped.")