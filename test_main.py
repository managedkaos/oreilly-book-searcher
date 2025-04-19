import urllib.parse
from unittest.mock import mock_open, patch

from main import (
    create_data_directory,
    extract_publication_date,
    find_best_match,
    read_titles,
    sanitize_filename,
    search_book,
)

# Test data
TEST_TITLE = "Head First Software Architecture"
TEST_PUB_DATE = "2024-03-06"
TEST_API_RESPONSE = {
    "results": [
        {
            "title": TEST_TITLE,
            "issued": f"{TEST_PUB_DATE}T00:00:00Z",
            "format": "book",
            "other_data": "irrelevant",
        },
        {
            "title": "Different Book",
            "issued": "2023-01-01T00:00:00Z",
            "format": "book",
        },
        {
            "title": "Not a Book",
            "issued": "2024-01-01T00:00:00Z",
            "format": "video",
        },
    ]
}


def test_read_titles():
    """Test reading titles from a file."""
    mock_file_content = f"{TEST_TITLE}\nO'Reilly\nEPUB\n12.8 MB\nPDF\n14.6 MB\n\n"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        titles = read_titles("dummy.txt")
        assert len(titles) == 1
        assert titles[0] == TEST_TITLE


def test_sanitize_filename():
    """Test filename sanitization."""
    expected = "Head-First-Software-Architecture.json"
    assert sanitize_filename(TEST_TITLE) == expected

    # Test with special characters
    assert sanitize_filename("Test & More!") == "Test-More.json"
    assert sanitize_filename("Multiple   Spaces") == "Multiple-Spaces.json"


def test_create_data_directory():
    """Test data directory creation."""
    with patch("os.makedirs") as mock_makedirs:
        create_data_directory()
        mock_makedirs.assert_called_once_with("./data", exist_ok=True)


@patch("requests.get")
@patch("builtins.open")
@patch("os.makedirs")
def test_search_book_api(mock_makedirs, mock_open, mock_get):
    """Test book search with mocked API response."""
    # Configure mock response
    mock_response = type(
        "MockResponse", (), {"status_code": 200, "json": lambda: TEST_API_RESPONSE}
    )
    mock_get.return_value = mock_response

    # Mock file write
    mock_file = mock_open.return_value.__enter__.return_value
    mock_file.write.return_value = None

    # Test successful search
    result = search_book(TEST_TITLE, use_cache=False)
    assert result == TEST_API_RESPONSE

    # Verify the URL includes the field parameter
    expected_url = f"https://learning.oreilly.com/api/v2/search/?query={urllib.parse.quote(TEST_TITLE)}&field=title"
    mock_get.assert_called_with(expected_url)

    # Verify file was written
    mock_open.assert_called_with("data/Head-First-Software-Architecture.json", "w")

    # Test failed search
    mock_response.status_code = 404
    result = search_book(TEST_TITLE, use_cache=False)
    assert result is None


def test_find_best_match():
    """Test finding the best matching book from results."""
    # Test with valid data
    best_match = find_best_match(TEST_TITLE, TEST_API_RESPONSE)
    assert best_match["title"] == TEST_TITLE
    assert best_match["issued"] == f"{TEST_PUB_DATE}T00:00:00Z"

    # Test with no results
    assert find_best_match(TEST_TITLE, {}) is None
    assert find_best_match(TEST_TITLE, {"results": []}) is None

    # Test with no books
    no_books = {
        "results": [
            {
                "title": "Not a Book",
                "issued": "2024-01-01T00:00:00Z",
                "format": "video",
            }
        ]
    }
    assert find_best_match(TEST_TITLE, no_books) is None

    # Test with multiple books, should pick newest
    multiple_books = {
        "results": [
            {
                "title": "Old Book",
                "issued": "2020-01-01T00:00:00Z",
                "format": "book",
            },
            {
                "title": "New Book",
                "issued": "2024-01-01T00:00:00Z",
                "format": "book",
            },
        ]
    }
    best_match = find_best_match("Book", multiple_books)
    assert best_match["title"] == "New Book"
    assert best_match["issued"] == "2024-01-01T00:00:00Z"


def test_extract_publication_date():
    """Test publication date extraction."""
    # Test successful extraction
    assert extract_publication_date(TEST_TITLE, TEST_API_RESPONSE) == TEST_PUB_DATE

    # Test missing results
    assert extract_publication_date(TEST_TITLE, {}) == "Not found"
    assert extract_publication_date(TEST_TITLE, {"results": []}) == "Not found"

    # Test missing issued date
    no_date_response = {"results": [{"title": TEST_TITLE, "format": "book"}]}
    assert extract_publication_date(TEST_TITLE, no_date_response) == "Not found"
