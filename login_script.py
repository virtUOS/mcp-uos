#!/usr/bin/env python3
"""
Login Form Extractor and Submitter

This script extracts the login form from a webpage using BeautifulSoup,
submits the form with user credentials using the requests library,
retrieves the session cookie, and then uses it to perform a search query.
"""

import os
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(".env")

# Configuration - Set your credentials here
USERNAME = os.getenv("UOS_MCP_USERNAME")
PASSWORD = os.getenv("UOS_MCP_PASSWORD")

# Search configuration
SEARCH_TERM = "Dienstreise"

# Base URL for the form action
BASE_URL = "https://www.uni-osnabrueck.de"


def extract_form_fields(html_content):
    """
    Extract all input fields from the login form using BeautifulSoup.

    Args:
        html_content: The HTML content as a string

    Returns:
        A tuple of (fields_dict, action_url, method)

    Raises:
        ValueError: If no login form is found in the HTML
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the login form - it has class="form" and target="_top"
    # or contains the username/password fields
    form = None

    # First, try to find by class and target attributes (login form specific)
    for f in soup.find_all('form'):
        if f.get('class') == ['form'] and f.get('target') == '_top':
            form = f
            break

    # Fallback: find by checking for 'user' or 'pass' input fields
    if not form:
        for f in soup.find_all('form'):
            has_user = f.find('input', {'name': 'user'}) or f.find('input', {'name': 'username'})
            has_pass = f.find('input', {'name': 'pass'}) or f.find('input', {'name': 'password'})
            if has_user and has_pass:
                form = f
                break

    if not form:
        raise ValueError("No login form found in HTML")

    fields = {}
    for input_field in form.find_all('input'):
        name = input_field.get('name')
        value = input_field.get('value', '')
        if name:
            fields[name] = value

    action = form.get('action', '') or ''
    method = form.get('method', 'get') or 'get'
    if isinstance(method, list):
        method = ' '.join(method)
    method = method.lower()

    return fields, action, method


def submit_login(form_data, username, password, action_url):
    """
    Submit login credentials and return session cookie.

    Args:
        form_data: Dictionary of form fields (including hidden fields)
        username: The username to submit
        password: The password to submit
        action_url: The form action URL (can be relative or absolute)

    Returns:
        A tuple of (response object, session object)
    """
    # Update form data with user credentials
    # The form uses 'user' for username and 'pass' for password
    form_data['user'] = username
    form_data['pass'] = password

    # Build full URL
    if action_url.startswith('http'):
        full_url = action_url
    else:
        full_url = BASE_URL + action_url

    # Send POST request
    session = requests.Session()
    response = session.post(full_url, data=form_data)

    return response, session


def fetch_html(url):
    """
    Fetch HTML content from a URL.

    Args:
        url: The URL to fetch

    Returns:
        The HTML content as a string
    """
    session = requests.Session()
    response = session.get(url)
    response.raise_for_status()
    return response.text


def main():
    """Main function to extract form, submit login, and print session cookie."""
    # Fetch HTML from URL
    print(f"Fetching login page from: {BASE_URL}/loginlogout")
    html_content = fetch_html(f"{BASE_URL}/loginlogout")

    # Extract form fields
    form_data, action, method = extract_form_fields(html_content)

    print(f"Extracted {len(form_data)} form fields")
    print(f"Form action: {action}")
    print(f"Form method: {method}")
    print()

    # Submit login
    response, session = submit_login(form_data, USERNAME, PASSWORD, action)

    # Print response status
    print(f"Response status: {response.status_code}")

    # Print response headers
    print("\nResponse headers:")
    for header, value in response.headers.items():
        print(f"  {header}: {value}")

    # Print all cookies
    print("\nAll cookies:")
    for cookie in session.cookies:
        print(f"  {cookie.name}={cookie.value}")

    # Check if login was successful by looking for error messages
    if response.status_code == 200:
        # Check if the response contains error messages (login failed)
        if "Benutzername" in response.text or "Passwort" in response.text:
            print("\nNote: Login may have failed (dummy credentials used)")
            print("The session cookie is still printed above for testing.")
        else:
            print("\nLogin successful!")
    elif response.status_code in [301, 302, 303, 307, 308]:
        print(f"\nRedirect to: {response.headers.get('Location', 'N/A')}")
        print("Note: The session cookie may be set after following redirects.")

    # Perform search using the authenticated session
    print()
    search_html = perform_search(session, SEARCH_TERM)

    # Extract and print search results
    print("\n" + "="*60)
    print(f"SEARCH RESULTS for: {SEARCH_TERM}")
    print("="*60)

    search_results = extract_search_results(search_html)
    print(f"Found {len(search_results)} results:\n")

    for i, result in enumerate(search_results, 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        if result['breadcrumbs']:
            print(f"   Breadcrumbs: {' > '.join(result['breadcrumbs'])}")
        else:
            print(f"   Breadcrumbs: (none)")
        if result['teaser']:
            print(f"   Teaser: {result['teaser'][:100]}..." if len(result['teaser']) > 100 else f"   Teaser: {result['teaser']}")
        else:
            print(f"   Teaser: (none)")
        print()

    # Fetch and print the first search result's content
    if search_results:
        print("\n" + "="*60)
        print("FETCHING FIRST RESULT:")
        print("="*60)

        first_result = search_results[0]
        print(f"Title: {first_result['title']}")
        print(f"URL: {first_result['url']}")
        print()

        # Fetch the page content
        page_html = fetch_page_content(session, first_result['url'])

        # Extract and print the main content as markdown
        markdown_content = extract_main_content_as_markdown(page_html)

        print("="*60)
        print("PAGE CONTENT (Markdown):")
        print("="*60)
        print(markdown_content)


def perform_search(session, search_term):
    """
    Perform a search using the authenticated session.

    Args:
        session: The requests Session object with authentication cookies
        search_term: The search term (URL encoded)

    Returns:
        The search results page content
    """
    # Build search parameters as a dictionary
    search_params = {
        'tx_solr[filter][0]': 'type:pages',
        'tx_solr[filter][1]': 'type:tx_solr_file',
        'tx_solr[resultsPerPage]': 50,
        'tx_solr[q]': search_term
    }

    # Build the URL
    search_url = f"{BASE_URL}/suche"

    print(f"Performing search for: {search_term}")
    print(f"Search URL: {search_url}")
    print(f"Search parameters: {search_params}")

    response = session.get(search_url, params=search_params)
    response.raise_for_status()

    return response.text


def extract_search_results(html_content):
    """
    Extract search results from HTML response.

    Args:
        html_content: The HTML content as a string

    Returns:
        A list of dictionaries, each containing:
        - title: The result title
        - url: The result URL
        - breadcrumbs: List of breadcrumb items (may be empty)
        - teaser: The teaser text (may be empty string)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Find all search results
    for result_div in soup.find_all('div', class_='search-result'):
        result = {
            'title': '',
            'url': '',
            'breadcrumbs': [],
            'teaser': ''
        }

        # Extract title and URL from results-topic
        topic = result_div.find('div', class_='results-topic')
        if topic:
            link = topic.find('a')
            if link:
                result['title'] = link.get_text(strip=True)
                result['url'] = link.get('href', '')

        # Extract breadcrumbs
        breadcrumb_nav = result_div.find('nav', class_='results-breadcrumbs') or result_div.find('div', class_='results-breadcrumbs')
        if breadcrumb_nav:
            for item in breadcrumb_nav.find_all('li', class_='breadcrumb-item'):
                breadcrumb_text = item.get_text(strip=True)
                if breadcrumb_text:
                    result['breadcrumbs'].append(breadcrumb_text)

        # Extract teaser
        teaser_div = result_div.find('div', class_='results-teaser')
        if teaser_div:
            result['teaser'] = teaser_div.get_text(strip=False).strip()

        results.append(result)

    return results


def fetch_page_content(session, url):
    """
    Fetch page content from a URL using the authenticated session.

    Args:
        session: The requests Session object with authentication cookies
        url: The URL to fetch (can be relative or absolute)

    Returns:
        The page content as a string
    """
    # Build full URL
    if url.startswith('http'):
        full_url = url
    else:
        full_url = BASE_URL + url

    response = session.get(full_url)
    response.raise_for_status()

    return response.text


def extract_main_content_as_markdown(html_content):
    """
    Extract main content from HTML and convert to markdown.

    Args:
        html_content: The HTML content as a string

    Returns:
        The main content as a markdown string
    """
    from markdownify import markdownify as md

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the main content element
    main_content = soup.find('main', id='main-content')

    if not main_content:
        return "No main content found."

    # Convert to markdown
    markdown_content = md(str(main_content))

    return markdown_content


if __name__ == "__main__":
    main()
