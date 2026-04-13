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
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")

# Fetch page content as markdown (single call)
markdown = client.fetch(results[0]['url'])
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

The server exposes two tools:

| Tool | Description |
|------|-------------|
| `uos_search` | Search the University of Osnabrück website for content |
| `uos_fetch` | Fetch page content from a URL and return it as markdown |

### MCP Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UOS_MCP_SERVER_HOST` | Host for HTTP transport | `127.0.0.1` |
| `UOS_MCP_SERVER_PORT` | Port for HTTP transport | (required for HTTP mode) |
| `UOS_MCP_USERNAME` | Your university username | `None` (required) |
| `UOS_MCP_PASSWORD` | Your university password | `None` (required) |

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

| Variable | Description | Default |
|----------|-------------|---------|
| `UOS_MCP_USERNAME` | Your university username | `None` (required) |
| `UOS_MCP_PASSWORD` | Your university password | `None` (required) |

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
