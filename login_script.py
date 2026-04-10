#!/usr/bin/env python3
"""
Login Form Extractor and Submitter

This script extracts the login form from an HTML file using BeautifulSoup,
submits the form with user credentials using the requests library,
and prints the session cookie to stdout.
"""

from bs4 import BeautifulSoup
import requests

# Configuration - Set your credentials here
USERNAME = "<user>"
PASSWORD = "<pass>"

# HTML file path
HTML_FILE = "loginlogout.html"

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


def main():
    """Main function to extract form, submit login, and print session cookie."""
    # Read HTML file
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
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


if __name__ == "__main__":
    main()
