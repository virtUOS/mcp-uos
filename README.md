# Login Script

## Overview

This script automates the login process to **Osnabrück University**'s website and performs a search query using authenticated session cookies.

## Functionality

1. Fetches the login page from `https://www.uni-osnabrueck.de/loginlogout`
2. Extracts the login form using BeautifulSoup
3. Submits login credentials via POST to obtain a session cookie
4. Performs a search query using the authenticated session

## Usage

```bash
python3 login_script.py
```
