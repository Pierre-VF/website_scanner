"""Module implementing the crawler
"""
import re
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .helpers import (
    extract_domain_from_url,
    headers_faking_navigator,
    list_of_unique_elements,
    sentence_from_element,
)


@dataclass
class ScrapingResult:
    url: str
    RESPONSE_CODE: int
    VALID: bool
    h1: list[str]
    h2: list[str]
    h3: list[str]
    p: list[str]
    images: list[str]
    images_url: list[str]
    emails: list[str]
    external_links: list[str]
    internal_links: list[str]
    css_links: list[str]
    script_links: list[str]
    response_time: timedelta = timedelta(seconds=0)


def is_absolute_url(url: str) -> bool:
    return url.startswith(("http:", "https:", "ftp:", "ftps:", "sftp:"))


def make_absolute_url(url: str, base_url: str) -> str:
    if url.startswith("/") or not is_absolute_url(url):
        out = urljoin(base_url, url)
    else:
        out = url
    return out


def get_interesting_page_contents(url: str) -> ScrapingResult:
    print(f"Scraping: {url}")
    try:
        headers = headers_faking_navigator()
        page = requests.get(url, headers=headers)
    except:
        return ScrapingResult(
            url=url,
            RESPONSE_CODE=0,
            VALID=False,
            h1=[],
            h2=[],
            h3=[],
            p=[],
            images=[],
            images_url=[],
            emails=[],
            external_links=[],
            internal_links=[],
            css_links=[],
            script_links=[],
        )

    out = {}
    out["url"] = url
    out["RESPONSE_CODE"] = page.status_code
    out["VALID"] = page.status_code == 200
    out["response_time"] = page.elapsed

    # Shortcut on images and stylesheets
    if url.endswith((".css", ".js", ".png", "jpg", ".jpeg", ".ico", ".svg")):
        return ScrapingResult(
            **out,
            h1=[],
            h2=[],
            h3=[],
            p=[],
            images=[],
            images_url=[],
            emails=[],
            external_links=[],
            internal_links=[],
            css_links=[],
            script_links=[],
        )

    soup = BeautifulSoup(page.content, "html.parser")
    for field_type in ["h1", "h2", "h3", "p"]:
        l = []
        xs = soup.find_all(field_type)
        for p in xs:
            s_i = sentence_from_element(p)
            l.append(s_i)
        out[field_type] = l

    images = []
    for i in soup.find_all("img"):
        try:
            images.append(i["src"])
        except:
            try:
                images.append(i["data-src"])
            except:
                pass
    out["images"] = images

    css_links = []
    for i in soup.find_all("link", rel="stylesheet"):
        try:
            css_link_i = make_absolute_url(i["href"], base_url=url)
            css_links.append(css_link_i)
        except:
            pass
    out["css_links"] = css_links

    script_links = []
    for i in soup.find_all("script", src=re.compile(".*")):
        try:
            script_i = make_absolute_url(i["src"], base_url=url)
            script_links.append(script_i)
        except:
            pass
    out["script_links"] = script_links

    images_url = []
    for i in images:
        if i.startswith("data:image"):
            pass  # Skip processing embedded images
        else:
            images_url.append(make_absolute_url(i, base_url=url))
    out["images_url"] = list_of_unique_elements(images_url)

    xs = soup.find_all("a", href=True)
    internal_links = []
    external_links = []
    email_addresses = []
    for p in xs:
        s_i = p["href"]
        if s_i.startswith("mailto:"):
            email_addresses.append(s_i.replace("mailto:", ""))
        else:
            external_links.append(make_absolute_url(s_i, base_url=url))

    # Reformatting external links
    current_domain = extract_domain_from_url(url)
    real_external_links = []
    real_internal_links = []
    for i in list_of_unique_elements(internal_links + external_links):
        if current_domain in i:
            real_internal_links.append(i)
        else:
            real_external_links.append(i)

    out["emails"] = list_of_unique_elements(email_addresses)
    out["external_links"] = real_external_links
    out["internal_links"] = real_internal_links
    return ScrapingResult(**out)


def crawl_website(url: str) -> dict[str, str]:
    crawled_internal_urls = []
    internal_urls_to_check = [url]
    crawled_external_urls = []
    external_urls_to_check = []

    res = dict()

    # Crawling internal links
    while len(internal_urls_to_check) > 0:
        url_i = internal_urls_to_check.pop(0)
        r_i = get_interesting_page_contents(url_i)
        crawled_internal_urls.append(url_i)
        res[url_i] = r_i
        # Adding internal urls
        for i in r_i.internal_links + r_i.images_url + r_i.css_links + r_i.script_links:
            if i in crawled_internal_urls:
                pass
            elif i in internal_urls_to_check:
                pass
            else:
                internal_urls_to_check.append(i)

        # Adding external urls
        for i in r_i.external_links:
            if i in crawled_external_urls:
                pass
            elif i in external_urls_to_check:
                pass
            else:
                external_urls_to_check.append(i)

    ext_res = dict()
    while len(external_urls_to_check) > 0:
        url_i = external_urls_to_check.pop(0)
        r_i = get_interesting_page_contents(url_i)
        crawled_external_urls.append(url_i)
        ext_res[url_i] = r_i
    res["external"] = ext_res

    return res
