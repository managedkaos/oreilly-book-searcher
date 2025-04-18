import json
import os
from unittest.mock import patch, mock_open
import pytest

from main import (
    read_titles,
    search_book,
    extract_publication_date,
    create_data_directory,
    sanitize_filename,
)

# Test data
TEST_TITLE = "Head First Software Architecture"
TEST_PUB_DATE = "2024-03-06"
TEST_API_RESPONSE = {
    "results": [
        {
            "title": TEST_TITLE,
            "issued": f"{TEST_PUB_DATE}T00:00:00Z",
            "other_data": "irrelevant"
        }
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
def test_search_book(mock_get):
    """Test book search with mocked API response."""
    # Configure mock response
    mock_response = type('MockResponse', (), {
        'status_code': 200,
        'json': lambda: TEST_API_RESPONSE
    })
    mock_get.return_value = mock_response

    # Test successful search
    result = search_book(TEST_TITLE)
    assert result == TEST_API_RESPONSE

    # Test failed search
    mock_response.status_code = 404
    result = search_book(TEST_TITLE)
    assert result is None

def test_extract_publication_date():
    """Test publication date extraction."""
    # Test successful extraction
    assert extract_publication_date(TEST_API_RESPONSE) == TEST_PUB_DATE

    # Test missing results
    assert extract_publication_date({}) == "Not found"
    assert extract_publication_date({"results": []}) == "Not found"

    # Test missing issued date
    no_date_response = {"results": [{"title": TEST_TITLE}]}
    assert extract_publication_date(no_date_response) == "Not found"
