#!/usr/bin/env python3
"""
Test script for the mcpuos package.

This script demonstrates how to use the UOSWebsiteClient class to:
1. Log in to the University of Osnabrück website
2. Perform a search
3. Fetch and display search results
4. Fetch and display content of a search result

Usage:
    python -m tests.search_and_fetch
    python tests/search_and_fetch.py
"""

import os
import sys

from dotenv import load_dotenv
from mcpuos import UOSWebsiteClient

load_dotenv()

def main():
    """Main function to demonstrate the mcpuos package functionality."""
    # Load credentials from environment
    username = os.getenv("UOS_MCP_USERNAME")
    password = os.getenv("UOS_MCP_PASSWORD")

    if not username or not password:
        print("Error: UOS_MCP_USERNAME and UOS_MCP_PASSWORD environment variables are required.")
        print("Please create a .env file with your credentials.")
        sys.exit(1)

    # Initialize the client
    client = UOSWebsiteClient(username=username, password=password)

    # Perform login
    print("Logging in...")
    client.login()
    print("Login successful!\n")

    # Perform search
    search_term = "Dienstreise"
    print(f"Performing search for: {search_term}")
    search_html = client.perform_search(search_term)

    # Extract and print search results
    search_results = client.extract_search_results(search_html)
    print(f"Found {len(search_results)} results:\n")

    for i, result in enumerate(search_results, 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        if result['breadcrumbs']:
            print(f"   Breadcrumbs: {' > '.join(result['breadcrumbs'])}")
        else:
            print(f"   Breadcrumbs: (none)")
        if result['teaser']:
            teaser = result['teaser']
            if len(teaser) > 100:
                teaser = teaser[:100] + "..."
            print(f"   Teaser: {teaser}")
        else:
            print(f"   Teaser: (none)")
        print()

    # Fetch and print the first search result's content
    if search_results:
        first_result = search_results[0]
        print("=" * 60)
        print("FETCHING FIRST RESULT:")
        print("=" * 60)
        print(f"Title: {first_result['title']}")
        print(f"URL: {first_result['url']}")
        print()

        # Fetch the page content
        page_html = client.fetch_page_content(first_result['url'])

        # Extract and print the main content as markdown
        markdown_content = client.extract_main_content_as_markdown(page_html)

        print("=" * 60)
        print("PAGE CONTENT (Markdown):")
        print("=" * 60)
        print(markdown_content)


if __name__ == "__main__":
    main()
