"""
Website interaction module for the University of Osnabrück.

This module provides the UOSWebsiteClient class for logging in, searching,
and fetching content from the university's website.
"""

import os
import time
import requests

from bs4 import BeautifulSoup
from markdownify import markdownify as md


class UOSWebsiteClient:
    """
    A client for interacting with the University of Osnabrück website.

    This class provides methods for logging in, performing searches, and
    fetching content from the university's website.
    """

    BASE_URL = "https://www.uni-osnabrueck.de"

    def __init__(self, username=None, password=None, base_url=None):
        """
        Initialize the UOSWebsiteClient.

        Args:
            username: The username for login. If None, reads from UOS_MCP_USERNAME env var.
            password: The password for login. If None, reads from UOS_MCP_PASSWORD env var.
            base_url: The base URL for the website. Defaults to BASE_URL.
        """
        self.username = username or os.getenv("UOS_MCP_USERNAME")
        self.password = password or os.getenv("UOS_MCP_PASSWORD")
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self._logged_in = False
        self._last_login = 0

    def login(self):
        """
        Perform login and establish a session.

        Returns:
            True if login was successful, False otherwise.
        """
        # Fetch login page
        response = requests.get(f"{self.base_url}/loginlogout")
        response.raise_for_status()
        html_content = response.text

        # Extract form fields
        form_data, action = self._extract_form_fields(html_content)

        # Build full action URL
        if action.startswith('http'):
            full_url = action
        else:
            full_url = self.base_url + action

        # Update form data with credentials
        form_data['user'] = self.username
        form_data['pass'] = self.password

        # Submit login
        response = self.session.post(full_url, data=form_data)
        response.raise_for_status()

        self._logged_in = True
        self._last_login = time.time()
        return True

    def _ensure_logged_in(self):
        """
        Check if the session is valid and login if necessary.

        A session is considered valid if the last login was within the last hour.
        """
        if time.time() - self._last_login > 3600:
            self.login()

    def _extract_form_fields(self, html_content):
        """
        Extract all input fields from the login form.

        Args:
            html_content: The HTML content as a string.

        Returns:
            A tuple of (fields_dict, action_url).

        Raises:
            ValueError: If no login form is found.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        form = None
        for f in soup.find_all('form'):
            has_user = f.find('input', {'name': 'user'})
            has_pass = f.find('input', {'name': 'pass'})
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

        action = form.get('action', '')

        return fields, action

    def _perform_search(self, search_term, results_per_page=50):
        """
        Perform a search using the authenticated session.

        Args:
            search_term: The search term.
            results_per_page: Number of results per page. Defaults to 50.

        Returns:
            The search results page content as a string.
        """
        search_params = {
            'tx_solr[filter][0]': 'type:pages',
            'tx_solr[filter][1]': 'type:tx_solr_file',
            'tx_solr[resultsPerPage]': results_per_page,
            'tx_solr[q]': search_term
        }

        search_url = f"{self.base_url}/suche"

        response = self.session.get(search_url, params=search_params)
        response.raise_for_status()

        return response.text

    def _extract_search_results(self, html_content):
        """
        Extract search results from HTML response.

        Args:
            html_content: The HTML content as a string.

        Returns:
            A list of dictionaries, each containing:
            - title: The result title
            - url: The result URL
            - breadcrumbs: List of breadcrumb items (may be empty)
            - teaser: The teaser text (may be empty string)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        for result_div in soup.find_all('div', class_='search-result'):
            result = {
                'title': '',
                'url': '',
                'breadcrumbs': [],
                'teaser': ''
            }

            topic = result_div.find('div', class_='results-topic')
            if topic:
                link = topic.find('a')
                if link:
                    result['title'] = link.get_text(strip=True)
                    result['url'] = link.get('href', '')

            breadcrumb_nav = result_div.find('nav', class_='results-breadcrumbs') or result_div.find('div', class_='results-breadcrumbs')
            if breadcrumb_nav:
                for item in breadcrumb_nav.find_all('li', class_='breadcrumb-item'):
                    breadcrumb_text = item.get_text(strip=True)
                    if breadcrumb_text:
                        result['breadcrumbs'].append(breadcrumb_text)

            teaser_div = result_div.find('div', class_='results-teaser')
            if teaser_div:
                result['teaser'] = teaser_div.get_text(strip=False).strip()

            results.append(result)

        return results

    def search(self, search_term, results_per_page=50):
        """
        Perform a search and return parsed results.

        This is a convenience method that combines _perform_search and
        _extract_search_results into a single call.

        Args:
            search_term: The search term.
            results_per_page: Number of results per page. Defaults to 50.

        Returns:
            A list of dictionaries, each containing:
            - title: The result title
            - url: The result URL
            - breadcrumbs: List of breadcrumb items (may be empty)
            - teaser: The teaser text (may be empty string)
        """
        self._ensure_logged_in()
        html_content = self._perform_search(search_term, results_per_page)
        return self._extract_search_results(html_content)

    def _fetch_page_content(self, url):
        """
        Fetch page content from a URL using the authenticated session.

        Args:
            url: The URL to fetch (can be relative or absolute).

        Returns:
            The page content as a string.
        """
        if url.startswith('http'):
            full_url = url
        else:
            full_url = self.base_url + url

        response = self.session.get(full_url)
        response.raise_for_status()

        return response.text

    def _extract_main_content_as_markdown(self, html_content):
        """
        Extract main content from HTML and convert to markdown.

        Args:
            html_content: The HTML content as a string.

        Returns:
            The main content as a markdown string.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        main_content = soup.find('main', id='main-content')

        if not main_content:
            return "No main content found."

        markdown_content = md(str(main_content))

        return markdown_content

    def fetch(self, url):
        """
        Fetch page content and return it as markdown.

        This is a convenience method that combines _fetch_page_content and
        _extract_main_content_as_markdown into a single call.

        Args:
            url: The URL to fetch (can be relative or absolute).

        Returns:
            The main content as a markdown string.
        """
        self._ensure_logged_in()
        html_content = self._fetch_page_content(url)
        return self._extract_main_content_as_markdown(html_content)
