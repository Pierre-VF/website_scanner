"""
Module with helper functions
"""
import re
from urllib.parse import urlparse


def list_of_unique_elements(x: list) -> list:
    return list(set(x))


def extract_email_address(x):
    return re.search(r"[\w\.-]+@[\w\.-]+[a-z]", x).group(0)


def extract_domain_from_url(url: str) -> str:
    return urlparse(url).netloc


def sentence_from_element(x: str) -> str:
    return " ".join(x.text.split())


def headers_faking_navigator() -> dict[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    return headers
