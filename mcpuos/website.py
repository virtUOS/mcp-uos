"""
Website interaction module for the Osnabrück University.

This module provides the UOSWebsiteClient class for logging in, searching,
and fetching content from the university's website.
"""

import os
import re
import time
import requests
import tempfile

from all2md import to_markdown
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urljoin, urlparse

from mcpuos.models import SearchResult, SearchResults, PersonSearchResult, PersonSearchResults, PersonDetails


class UOSWebsiteClient:
    """
    A client for interacting with the Osnabrück University website.

    This class provides methods for logging in, performing searches, and
    fetching content from the university's website.
    """

    BASE_URL = "https://www.uni-osnabrueck.de"

    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def __init__(self, username=None, password=None, base_url=None, skip_login=None):
        """
        Initialize the UOSWebsiteClient.

        Args:
            username: The username for login. If None, reads from UOS_MCP_USERNAME env var.
            password: The password for login. If None, reads from UOS_MCP_PASSWORD env var.
            base_url: The base URL for the website. Defaults to BASE_URL.
            skip_login: If True, skip authentication entirely (public content only).
                        If None, reads from UOS_MCP_SKIP_LOGIN env var. Defaults to False.
        """
        self.username = username or os.getenv("UOS_MCP_USERNAME")
        self.password = password or os.getenv("UOS_MCP_PASSWORD")
        self.base_url = base_url or self.BASE_URL
        if skip_login is None:
            skip_login = os.getenv("UOS_MCP_SKIP_LOGIN", "").lower() in ("1", "true", "yes")
        self.skip_login = skip_login
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self._last_login = 0

    def login(self):
        """
        Perform login and establish a session.

        Returns:
            True if login was successful, False otherwise.
        """
        # Fetch login page
        response = requests.get(f"{self.base_url}/loginlogout",
                                headers=self.DEFAULT_HEADERS)
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

        self._last_login = time.time()
        return True

    def _ensure_logged_in(self):
        """
        Check if the session is valid and login if necessary.

        A session is considered valid if the last login was within the last 23h.
        When skip_login is True, this method does nothing (public content only).
        """
        if self.skip_login:
            return
        if time.time() - self._last_login > (23 * 60 * 60):
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
            results_per_page: Number of results per page. Can be 10, 25 or 50. Defaults to 50.

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

    def _extract_search_results(self, html_content) -> list[SearchResult]:
        """
        Extract search results from HTML response.

        Args:
            html_content: The HTML content as a string.

        Returns:
            A list of SearchResult objects.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        for result_div in soup.find_all('div', class_='search-result'):
            title = ''
            url = ''
            breadcrumbs = []
            teaser = ''

            topic = result_div.find('div', class_='results-topic')
            if topic:
                link = topic.find('a')
                if link:
                    title = link.get_text(strip=True)
                    url = urljoin(self.base_url, str(link.get('href', '')))

            breadcrumb_nav = result_div.find('nav', class_='results-breadcrumbs') or result_div.find('div', class_='results-breadcrumbs')
            if breadcrumb_nav:
                for item in breadcrumb_nav.find_all('li', class_='breadcrumb-item'):
                    breadcrumb_text = item.get_text(strip=True)
                    if breadcrumb_text:
                        breadcrumbs.append(breadcrumb_text)

            teaser_div = result_div.find('div', class_='results-teaser')
            if teaser_div:
                teaser = teaser_div.get_text(strip=False).strip()

            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    breadcrumbs=breadcrumbs,
                    teaser=teaser
                )
            )

        return results

    def search(self, search_term, results_per_page=50) -> SearchResults:
        """
        Perform a search and return parsed results.

        This is a convenience method that combines _perform_search and
        _extract_search_results into a single call.

        Args:
            search_term: The search term.
            results_per_page: Number of results per page. Can be 10, 25 or 50. Defaults to 50.

        Returns:
            A SearchResults object containing the list of results and metadata.
        """
        self._ensure_logged_in()

        # Match the next best available parameter
        # Everything else will fall back to 10 results.
        if results_per_page > 50:
            results_per_page = 50
        elif results_per_page > 25:
            results_per_page = 25

        html_content = self._perform_search(search_term, results_per_page)
        results = self._extract_search_results(html_content)

        return SearchResults(
            results=results,
            query=search_term,
            total_count=len(results)
        )

    def _fetch_page_content(self, url):
        """
        Fetch page content from a URL using the authenticated session.

        Args:
            url: The URL to fetch (can be an absolute path or a URL)

        Returns:
            A tuple of (content, content_type).
            - content: The page content as string (for HTML) or bytes (for PDF)
            - content_type: The content-type header value
        """
        if url.startswith('/'):
            url = self.base_url + url
        elif not url.startswith('http://') and not url.startswith('https://'):
            raise ValueError(f"URL must be absolute path or URL: {url}")

        response = self.session.get(url)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        is_text = 'text/' in content_type

        # Use response.content for binary files (PDF), response.text for text files (HTML)
        content = response.text if is_text else response.content

        return content, content_type

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

        # Make link absolute
        # Replace with markdownify-internal functionality one #260 is merged:
        # https://github.com/matthewwithanm/python-markdownify/pull/260
        for link in main_content.find_all('a'):
            href = link.get('href')
            if not href or urlparse(str(href)).netloc:
                continue
            link['href'] = urljoin(self.base_url, str(href))

        markdown_content = md(str(main_content))

        return markdown_content

    def _convert_pdf_to_markdown(self, pdf_content):
        """
        Convert PDF content to markdown.

        Args:
            pdf_content: The PDF content as bytes.

        Returns:
            The content as a markdown string.
        """
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name
            return to_markdown(tmp_path)

    PEOPLE_SEARCH_URL = "/kontakt/personensuche"
    PEOPLE_DETAILS_PREFIX = "https://www.uni-osnabrueck.de/kontakt/personensuche/personendetails"

    def people_search(self, query: str) -> PersonSearchResults:
        """
        Search for people employed at the Osnabrück University.

        Args:
            query: Name or partial name to search for.

        Returns:
            A PersonSearchResults object with matching people and their detail URLs.
        """
        response = self.session.post(
            self.base_url + self.PEOPLE_SEARCH_URL,
            data={"command": "search_key", "search_key": query, "search": "Suche starten"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        results_box = soup.select_one("div.box.extern")
        if results_box:
            for link in results_box.select(".linkliste ul li a"):
                name = link.get_text(strip=True)
                href = urljoin(self.base_url, str(link.get("href", "")))
                results.append(PersonSearchResult(name=name, details_url=href))

        total_count = len(results)
        count_p = results_box.find("p") if results_box else None
        if count_p:
            # "Einträge 1 bis 25 von 42" or "Einträge 1 bis 3"
            m = re.search(r"von\s+(\d+)", count_p.get_text())
            if m:
                total_count = int(m.group(1))

        return PersonSearchResults(results=results, query=query, total_count=total_count)

    def list_people_by_letter(self, letter: str, delay: float = 0.0) -> list[PersonSearchResult]:
        """
        List all people whose surname starts with the given letter.

        Follows pagination to the end by repeatedly clicking the "»" (next)
        link found in the result box, which avoids having to reconstruct the
        site's own `page`/`cHash` query parameters.

        Args:
            letter: A single letter, e.g. "A".
            delay: Seconds to sleep between page fetches (be polite to the server).

        Returns:
            A list of PersonSearchResult objects, one per person found.
        """
        results = []
        url = self.base_url + self.PEOPLE_SEARCH_URL
        params = {"command": "starting_with", "search_key": letter}

        while True:
            response = self.session.get(url, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results_box = soup.select_one("div.box.extern")
            if not results_box:
                break

            for link in results_box.select(".linkliste ul li a"):
                name = link.get_text(strip=True)
                href = urljoin(self.base_url, str(link.get("href", "")))
                results.append(PersonSearchResult(name=name, details_url=href))

            next_link = None
            for a in results_box.find_all("a"):
                if a.get_text(strip=True) in (">>", "»"):
                    next_link = a
                    break

            if not next_link or not next_link.get("href"):
                break

            url = urljoin(self.base_url, str(next_link["href"]))
            params = None

            if delay:
                time.sleep(delay)

        return results

    def list_all_people(self, delay: float = 0.0) -> list[PersonSearchResult]:
        """
        List all people in the Personensuche directory, A to Z.

        Args:
            delay: Seconds to sleep between HTTP requests (be polite to the server).

        Returns:
            A de-duplicated list of PersonSearchResult objects (by details_url).
        """
        seen = set()
        results = []

        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            for person in self.list_people_by_letter(letter, delay=delay):
                if person.details_url in seen:
                    continue
                seen.add(person.details_url)
                results.append(person)

            if delay:
                time.sleep(delay)

        return results

    def people_details(self, url: str) -> PersonDetails:
        """
        Fetch full contact details for a single person.

        Args:
            url: The details_url from a PersonSearchResult. Must start with
                 https://www.uni-osnabrueck.de/kontakt/personensuche/personendetails

        Returns:
            A PersonDetails object with all available contact fields.

        Raises:
            ValueError: If the URL does not point to the person details endpoint.
        """
        if not url.startswith(self.PEOPLE_DETAILS_PREFIX):
            raise ValueError(
                f"Invalid URL. Must start with {self.PEOPLE_DETAILS_PREFIX}"
            )

        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        box = soup.select_one("div.box.extern")
        if not box:
            raise ValueError("Person details block not found in response")

        name = box.find("h4").get_text(strip=True) if box.find("h4") else ""

        paragraphs = box.find_all("p")

        # First <p>: department lines then street + city (separated by <br>)
        department = None
        address = None
        if paragraphs:
            lines = [s.strip() for s in paragraphs[0].strings if s.strip()]
            if len(lines) >= 2:
                department = lines[0]
                address = ", ".join(lines[1:])
            elif lines:
                department = lines[0]

        # Second <p>: optional room, phone, fax, email — detected by label text.
        # Phone is inside an <abbr> tag so we handle it separately.
        room = phone = fax = email = None
        if len(paragraphs) > 1:
            p2 = paragraphs[1]

            # Phone: <abbr title="Telefon">Tel.</abbr>: <number>
            abbr = p2.find("abbr", title="Telefon")
            if abbr and abbr.next_sibling:
                phone = str(abbr.next_sibling).lstrip(":").strip()

            block_text = p2.get_text(separator="\n")
            for line in block_text.splitlines():
                line = line.strip()
                if line.startswith("Raum:"):
                    room = line.removeprefix("Raum:").strip()
                elif line.startswith("Fax:"):
                    fax = line.removeprefix("Fax:").strip()

            mail_tag = p2.find("a", class_="mail")
            if mail_tag:
                email = mail_tag.get_text(strip=True)

        # Remaining <p> blocks: look for a plain hyperlink as website
        website = None
        for p in paragraphs[2:]:
            link = p.find("a")
            if link and not link.get("class"):
                website = link.get("href") or link.get_text(strip=True)
                break

        return PersonDetails(
            name=name,
            department=department,
            address=address,
            room=room,
            phone=phone,
            fax=fax,
            email=email,
            website=website,
            source_url=url,
        )

    def fetch(self, url):
        """
        Fetch page content and return it as markdown.

        This is a convenience method that combines _fetch_page_content and
        _extract_main_content_as_markdown into a single call.

        Args:
            url: The URL to fetch (can be relative or absolute).

        Returns:
            The main content as a markdown string.

        Raises:
            ValueError: If the content type is not supported.
        """
        self._ensure_logged_in()
        content, content_type  = self._fetch_page_content(url)

        if 'text/html' in content_type:
            return self._extract_main_content_as_markdown(content)
        elif 'application/pdf' in content_type:
            return self._convert_pdf_to_markdown(content)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
