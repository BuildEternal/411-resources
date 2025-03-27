import pytest
import requests

from boxing.utils.api_utils import get_random

# A valid random number (as a string) returned by random.org
RANDOM_NUMBER_STR = "0.55"
RANDOM_NUMBER = 0.55

@pytest.fixture
def mock_random_org(mocker):
    # Create a mock response object with a valid random number as text
    mock_response = mocker.Mock()
    mock_response.text = RANDOM_NUMBER_STR
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_random(mock_random_org):
    """Test retrieving a random float from random.org."""
    result = get_random()

    # Assert that the result matches the mocked random number
    assert result == RANDOM_NUMBER, f"Expected random number {RANDOM_NUMBER}, but got {result}"

    # Ensure that the correct URL was called
    expected_url = "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new"
    requests.get.assert_called_once_with(expected_url, timeout=5)

def test_get_random_request_failure(mocker):
    """Test handling of a request failure when calling random.org."""
    # Simulate a request failure by raising a RequestException
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random()

def test_get_random_timeout(mocker):
    """Test handling of a timeout when calling random.org."""
    # Simulate a timeout exception
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()

def test_get_random_invalid_response(mock_random_org):
    """Test handling of an invalid response from random.org."""
    # Simulate an invalid response (non-numeric)
    mock_random_org.text = "invalid_response"

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()
