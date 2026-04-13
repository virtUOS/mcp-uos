# mcpuos Package

A Python package for interacting with the University of Osnabrück website.

## Overview

The `mcpuos` package provides functionality for:
- Logging in to the University of Osnabrück website
- Performing authenticated searches
- Fetching and converting page content to markdown

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
│   └── website.py      # Core functionality
├── tests/              # Test scripts (outside package)
│   └── search_and_fetch.py
├── .env.sample         # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

See [`requirements.txt`](requirements.txt) for the list of dependencies.
