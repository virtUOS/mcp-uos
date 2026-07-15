# mcpuos Package

A Python package for interacting with the University of Osnabrück website.

## Overview

The `mcpuos` package provides functionality for:
- Logging in to the University of Osnabrück website
- Performing authenticated searches
- Fetching and converting page content to markdown
- Running as an MCP server for LLM integration

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from mcpuos import UOSWebsiteClient

# Initialize the client with your credentials
client = UOSWebsiteClient(username="your_username", password="your_password")

# Perform login
# This is optional since search(…) and fetch(…) will ensure an active login.
client.login()

# Perform a search (returns parsed results directly)
results = client.search("Dienstreise")

# Display results
for result in results.results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")

# Fetch page content as markdown (single call)
markdown = client.fetch(results.results[0].url)
print(markdown)
```

### Using Environment Variables

You can also configure the client using environment variables:

```python
import os
from mcpuos import UOSWebsiteClient

# Set environment variables
os.environ["UOS_MCP_USERNAME"] = "your_username"
os.environ["UOS_MCP_PASSWORD"] = "your_password"

# Initialize without credentials (reads from environment)
client = UOSWebsiteClient()
client.login()
```

## Running as MCP Server

The package includes an MCP server that exposes tools for LLM integration.

### stdio Transport (Default)

By default, the server uses stdio transport for local integration:

```bash
# Run the MCP server
python -m mcpuos

# Or directly
python mcpuos/mcp_server.py
```

### HTTP Transport

To run the server with HTTP transport, set the `UOS_MCP_SERVER_HOST` and `UOS_MCP_SERVER_PORT` environment variables:

```bash
# Start HTTP server on port 8000
export UOS_MCP_SERVER_HOST="127.0.0.1"
export UOS_MCP_SERVER_PORT="8000"
python -m mcpuos

# Or in one line
UOS_MCP_SERVER_HOST="127.0.0.1" UOS_MCP_SERVER_PORT="8000" python -m mcpuos
```

The server will be available at `http://127.0.0.1:8000/mcp`.

### MCP Tools

The server exposes three tools:

| Tool                  | Description                                                       |
|-----------------------|-------------------------------------------------------------------|
| `uos_search`          | Search the Osnabrück University website for content               |
| `uos_fetch`           | Fetch a university page as markdown (university URLs only)        |
| `uos_people_search`   | Search for people by name; returns full contact details inline    |

`uos_people_search` answers from a local pre-scraped snapshot (see
[People Search](#people-search) below) rather than querying the live
website.

## Running with Docker

Prebuilt images are published to `ghcr.io/virtuos/mcp-uos` (the commands below also work
with Podman). The image starts the MCP server on HTTP transport, listening on port 8000.

The server refuses to start without the pre-scraped people snapshot (see
[People Search](#people-search)), so mount a data directory into the container at
`/app/data` and bootstrap it once:

```bash
# 1. One-time bootstrap: the scraper itself needs the data file to exist
#    before it can start (the package loads it at import time).
mkdir -p data && echo '{"people": []}' > data/people.json

# 2. Build a real snapshot (public endpoints, no credentials required).
docker run --rm -v "$(pwd)/data:/app/data" ghcr.io/virtuos/mcp-uos mcp-uos-scrape-people

# 3. Start the MCP server.
docker run -d --name mcp-uos -p 8000:8000 -v "$(pwd)/data:/app/data" \
    -e UOS_MCP_USERNAME="your_username" -e UOS_MCP_PASSWORD="your_password" \
    ghcr.io/virtuos/mcp-uos
```

The server is then available at `http://127.0.0.1:8000/mcp`. Instead of passing
credentials, you can use `-e UOS_MCP_SKIP_LOGIN=true` for public content only, or pass
a prepared environment file with `--env-file .env`. On SELinux systems (e.g. Fedora
with Podman), append `:z` to the volume mounts (`-v "$(pwd)/data:/app/data:z"`).

To pick up a fresh snapshot, re-run step 2 periodically (e.g. from cron) and tell the
running server to reload the file without a restart:

```bash
docker kill --signal=HUP mcp-uos
```

## Scraping the People Directory

The Personensuche only supports on-demand name search, which isn't suitable for building a full
directory. `mcp-uos-scrape-people` walks the public A-Z listing instead, fetches full contact details
for every person, and writes the result to a JSON file:

```bash
mcp-uos-scrape-people
```

The endpoints scraped here (the alphabetical listing and person detail pages) are public, so no
credentials are required. The output file has the shape:

```json
{
  "scraped_at": "2026-07-14T12:00:00+00:00",
  "count": 5000,
  "people": [
    { "name": "...", "department": "...", "address": "...", "room": "...",
      "phone": "...", "fax": "...", "email": "...", "website": "...", "source_url": "..." }
  ]
}
```

This script has no built-in scheduler; run it periodically via an external cron job or systemd timer,
e.g.:

```
0 3 * * * /path/to/venv/bin/mcp-uos-scrape-people >> /var/log/mcp-uos-scrape.log 2>&1
```

Note: the package currently loads the people snapshot at import time, so on a fresh
install `mcp-uos-scrape-people` itself will not start while the data file is missing.
Create an empty stub once before the first scrape:

```bash
mkdir -p data && echo '{"people": []}' > data/people.json
```

## People Search

`uos_people_search` always answers from the JSON file written by
`mcp-uos-scrape-people` (path taken from `UOS_MCP_PEOPLE_DATA_PATH`) rather
than querying the live website, and returns full contact details inline
for every match (case-insensitive substring match against the name).

The data file is loaded once at startup; a missing or unreadable file is a
fatal startup error — the server won't run without a scraped snapshot in
place. To pick up a fresh scrape without restarting the server, send it
`SIGHUP` (e.g. `kill -HUP <pid>`) — this reloads the JSON file in place. If
the reload fails (file missing or corrupt at reload time), the server logs
the error and keeps serving the previously loaded data.

## Running the Test Script

To run the test script that demonstrates all functionality:

```bash
python tests/search_and_fetch.py
```

Or using Python module syntax:

```bash
python -m tests.search_and_fetch
```

## Configuration

The package can be configured using environment variables. You can either set them directly in your shell or use a `.env` file.

### Environment Variables

| Variable                        | Description                                        | Default                    |
|----------------------------------|----------------------------------------------------|----------------------------|
| `UOS_MCP_USERNAME`               | Username of UOS account                            | `None` (required)          |
| `UOS_MCP_PASSWORD`               | Password of UOS account                            | `None` (required)          |
| `UOS_MCP_SKIP_LOGIN`             | Skip authentication (public content only)          | `false`                    |
| `UOS_MCP_SERVER_HOST`            | Host for HTTP transport                            | `127.0.0.1`                |
| `UOS_MCP_SERVER_PORT`            | Port for HTTP transport                            | `None` (enables HTTP mode) |
| `UOS_MCP_PEOPLE_DATA_PATH`       | Data file for `uos_people_search` and the scraper  | `./data/people.json`       |
| `UOS_MCP_SCRAPE_DELAY_SECONDS`   | Delay between requests in `mcp-uos-scrape-people`  | `0.3`                      |

### Using a .env File

Create a `.env` file in the project directory with your credentials. See [`.env.sample`](.env.sample) for a template.

```bash
UOS_MCP_USERNAME="your_username"
UOS_MCP_PASSWORD="your_password"
```

## Package Structure

```
mcp-uos/
├── mcpuos/              # Package directory
│   ├── __init__.py     # Package initializer
│   ├── website.py      # Core functionality (UOSWebsiteClient)
│   ├── people_data.py  # PeopleDataStore for scrape mode
│   ├── mcp_server.py   # MCP server implementation
│   └── __main__.py     # MCP server entry point
├── tests/              # Test scripts (outside package)
│   └── search_and_fetch.py
├── .env.sample         # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

See [`requirements.txt`](requirements.txt) for the list of dependencies.
