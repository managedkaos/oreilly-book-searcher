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


def find_best_match(title: str, book_data: Dict) -> Dict:
    """Find the best matching book from the search results based on criteria:
    1. Must be a book format
    2. Title should match as closely as possible
    3. Among matching titles, choose the newest publication
    """
    if not book_data or "results" not in book_data or not book_data["results"]:
        logger.debug("No book data or results found")
        return None

    logger.debug(f"Considering {len(book_data['results'])} results")
    for result in book_data["results"]:
        logger.debug(f"Title: {result.get('title')}; Issued: {result.get('issued')}")

    # Filter for books only and create a list of candidates
    candidates = []
    for result in book_data["results"]:
        if result.get("format") != "book":
            continue

        # Store candidate with match info
        candidates.append({"result": result, "issued": result.get("issued", "")})

    if not candidates:
        logger.debug("No book format results found")
        return None

    logger.debug(f"Found {len(candidates)} candidates")
    for candidate in candidates:
        logger.debug(
            f"Candidate title: {candidate['result'].get('title')}, Issued: {candidate['issued']}"
        )

    # Sort candidates by publication date (newest first)
    def get_sort_key(candidate):
        try:
            # Extract date part and parse it
            date_str = candidate["issued"].split("T")[0]
            return time.strptime(date_str, "%Y-%m-%d")
        except (AttributeError, ValueError, IndexError):
            # If date is missing or malformed, put it at the end
            return time.strptime("1900-01-01", "%Y-%m-%d")

    candidates.sort(key=get_sort_key, reverse=True)
    best_match = candidates[0]["result"]
    logger.debug(
        f"Selected best match: {best_match.get('title')} (issued: {best_match.get('issued')})"
    )
    return best_match


def extract_publication_date(title: str, book_data: Dict) -> str:
    """Extract the publication date from the best matching book data."""
    best_match = find_best_match(title, book_data)

    if not best_match or "issued" not in best_match:
        logger.debug("No publication date found in book data")
        return "Not found"

    pub_date = best_match["issued"].split("T")[0]
    logger.debug(f"Found publication date: {pub_date}")
    return pub_date


def search_book(title: str, use_cache: bool = False) -> Dict:
    """Search for a book by title using the O'Reilly API or cached results."""
    logger.debug(f"Searching for book: {title}")

    if use_cache:
        # Try to load from cache
        filename = sanitize_filename(title)
        filepath = os.path.join("data", filename)

        if os.path.exists(filepath):
            logger.debug(f"Loading cached result from {filepath}")
            try:
                with open(filepath, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse cached file {filepath}, falling back to API"
                )
            except Exception as e:
                logger.warning(
                    f"Error reading cached file {filepath}: {e}, falling back to API"
                )
        else:
            logger.debug(f"No cached result found at {filepath}, using API")

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

        logger.debug(f"Saved result to {filepath}")

        return response.json()
    else:
        logger.error(f"Error searching for {title}: {response.status_code}")
        return None


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
    # Check if we should use cached results
    use_cache = os.getenv("USE_CACHE", "False").lower() == "true"

    logger.debug("Starting book search script")

    # Create data directory
    create_data_directory()

    # Read titles from file
    titles = read_titles("titles.txt")

    # Dictionary to store results
    results = {}

    # Search for each title
    for title in titles:
        logger.debug(f"Processing title: {title}")

        # Make API request
        book_data = search_book(title, use_cache)

        # Extract and print publication date
        pub_date = extract_publication_date(title, book_data)
        results[title] = pub_date

        # Print progress to STDOUT
        print(f"{title}: {pub_date}")

        if not use_cache:
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
