# Login Script

## Overview

This script automates the login process to **Osnabrück University**'s website and performs a search query using authenticated session cookies. It extracts the login form, submits credentials, and then uses the resulting session to search the university's website and display results in a readable format.

## Functionality

1. Fetches the login page from `https://www.uni-osnabrueck.de/loginlogout`
2. Extracts the login form using BeautifulSoup
3. Submits login credentials via POST to obtain a session cookie
4. Performs a search query using the authenticated session
5. Displays search results with titles, URLs, breadcrumbs, and teasers
6. Fetches and converts the first search result's content to markdown

## Usage

```bash
python3 login_script.py
```

## Configuration

The script can be configured using environment variables. You can either set them directly in your shell or use a `.env` file.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UOS_MCP_USERNAME` | Your university username | `"user"` |
| `UOS_MCP_PASSWORD` | Your university password | `"secret"` |

### Using a .env File

Create a `.env` file in the project directory with your credentials.
See [`.env.sample`](.env.sample) for a template.

```bash
UOS_MCP_USERNAME="your_username"
UOS_MCP_PASSWORD="your_password"
```

## Requirements

See [`requirements.txt`](requirements.txt) for the list of dependencies.
