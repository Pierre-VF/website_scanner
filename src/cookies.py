"""Module checking usage of cookies
"""

import requests

from .helpers import headers_faking_navigator


def page_uses_cookies(url) -> tuple[int, dict]:
    session = requests.Session()
    cookies_before = session.cookies.get_dict()
    assert cookies_before == {}
    response = session.get(url, headers=headers_faking_navigator())
    response.raise_for_status()
    cookies_after = session.cookies.get_dict()
    return len(cookies_after), cookies_after


if __name__ == "__main__":
    hostname_using_cookies = "https://www.easyjet.com/"
    url = "https://www.pierrevf.consulting/"
    n, details = page_uses_cookies(url)
    print(n)
