"""
Module with helper functions
"""

import re
from urllib.parse import urlparse

from markdownify import markdownify


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


def minimal_url(x: str) -> str:
    parsed_url = urlparse(x)

    out = f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"
    # if out.endswith("/"):
    #    out = out[:-1]
    return out


def html_to_markdown(x: str, clean: bool = True, remove_images: bool = True) -> str:
    out = markdownify(x)

    if clean:
        out = re.sub("(\\n){2,}", "\n\n", out)
    if remove_images:
        out = re.sub(
            "!\[[^(\[\])]*\]\([^(\[\])]*\)",
            "[image]",
            re.sub("(\\n){2,}", "\n\n", out),
        )
    return out
