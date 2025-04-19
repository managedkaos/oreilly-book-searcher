# O'Reilly Book Searcher

A Python application that uses the O'Reilly API to search for book metadata.

## Usage

1. Create a file named `titles.txt` in the same directory as the script. This file should contain a list of book titles separated by newlines. For example:

  ```text
  Building Multi-Tenant SaaS Architectures

  Software Architecture Patterns, 2nd Edition
  ```

1. Create a directory named `data` in the same directory as the `titles.txt` file. This directory will be used to store the downloaded book metadata.

  ```bash
  mkdir ./data
  ```

1. Run the application using Docker.


  ```bash
  docker run -it --rm -e DEBUG=True -e USE_CACHE=True \
    --volume ${PWD}/titles.txt:/work/titles.txt:ro \
    --volume ${PWD}/data:/work/data \
    ghcr.io/managedkaos/oreilly-book-searcher:main \
  ```

  _NOTE: The `DEBUG` and `USE_CACHE` environment variables are optional. If `DEBUG` is set to `True`, the application will print debug information to the console. If `USE_CACHE` is set to `True`, the application will use cached data if available._

1. Output is written to STDOUT and saved in `./data/publication_dates.json`.
