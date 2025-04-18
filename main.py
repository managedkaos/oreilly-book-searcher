import json
import logging
import os
import time
import urllib.parse
from typing import Dict, List

import requests

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") == "True" else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def read_titles(filename: str) -> List[str]:
    """Read book titles from a file, keeping only the first line of each book entry."""
    logger.debug(f"Reading titles from file: {filename}")
    titles = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if line:  # If line is not empty
                logger.debug(f"Found title: {line}")
                titles.append(line)
                # Skip the rest of the book entry until we hit an empty line
                while True:
                    next_line = f.readline().strip()
                    if not next_line:  # Found empty line, break to get next title
                        break
    logger.debug(f"Successfully read {len(titles)} titles from file")
    return titles


def search_book(title: str) -> Dict:
    """Search for a book by title using the O'Reilly API."""
    logger.debug(f"Searching for book: {title}")

    # URL encode the title to handle all special characters
    encoded_title = urllib.parse.quote(title)
    url = (
        f"https://learning.oreilly.com/api/v2/search/?query={encoded_title}&field=title"
    )

    response = requests.get(url)

    if response.status_code == 200:
        logger.debug(f"Successfully retrieved data for: {title}")

        # Save individual result to JSON file
        filename = sanitize_filename(title)
        filepath = os.path.join("data", filename)

        with open(filepath, "w") as f:
            json.dump(response.json(), f, indent=2)

        logger.debug(f"Saved individual result to {filepath}")

        return response.json()
    else:
        logger.error(f"Error searching for {title}: {response.status_code}")
        return None


def extract_publication_date(book_data: Dict) -> str:
    """Extract the publication date from the book data."""
    if not book_data or "results" not in book_data or not book_data["results"]:
        logger.debug("No book data or results found")
        return "Not found"

    # Get the first result (most relevant)
    first_result = book_data["results"][0]
    if "issued" in first_result:
        pub_date = first_result["issued"].split("T")[0]
        logger.debug(f"Found publication date: {pub_date}")
        return pub_date
    logger.debug("No publication date found in book data")
    return "Not found"


def create_data_directory():
    """Create the data directory if it doesn't exist."""
    data_dir = "./data"

    logger.debug(f"Creating data directory: {data_dir}")
    os.makedirs(data_dir, exist_ok=True)


def sanitize_filename(title: str) -> str:
    """Convert title to a safe filename by replacing spaces and special characters with dashes."""

    # Replace spaces and special characters with dashes
    safe_name = "".join(c if c.isalnum() else "-" for c in title)

    # Remove consecutive dashes
    safe_name = "-".join(filter(None, safe_name.split("-")))
    return f"{safe_name}.json"


def main():
    logger.debug("Starting book search script")

    # Create data directory
    create_data_directory()

    # Read titles from file
    titles = read_titles("titles.txt")

    # Dictionary to store results
    results = {}

    # Search for each title
    for title in titles:
        logger.debug(f"\nProcessing title: {title}")

        # Make API request
        book_data = search_book(title)

        # Extract and print publication date
        pub_date = extract_publication_date(book_data)
        results[title] = pub_date

        # Print progress to STDOUT
        print(f"{title}: {pub_date}")

        # Wait 1 second between requests to respect rate limits
        logger.debug("Waiting 1 second before next request")
        time.sleep(1)

    # Save all results to JSON file
    summary_filepath = os.path.join("data", "publication_dates.json")
    with open(summary_filepath, "w") as f:
        json.dump(results, f, indent=2)
    logger.debug(f"Results saved to {summary_filepath}")

    logger.debug("Script completed successfully")


if __name__ == "__main__":
    main()
