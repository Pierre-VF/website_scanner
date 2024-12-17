"""Module implementing the crawler"""

import re
from dataclasses import dataclass, field
from datetime import timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .helpers import (
    extract_domain_from_url,
    headers_faking_navigator,
    html_to_markdown,
    list_of_unique_elements,
    minimal_url,
    sentence_from_element,
)


@dataclass
class ScrapingResult:
    url: str
    RESPONSE_CODE: int
    VALID: bool
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    h3: list[str] = field(default_factory=list)
    p: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    images_url: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    css_links: list[str] = field(default_factory=list)
    script_links: list[str] = field(default_factory=list)
    response_time: timedelta = timedelta(seconds=0)
    text_as_markdown: str | None = None
    exception: Exception | None = None


def is_absolute_url(url: str) -> bool:
    return url.startswith(("http:", "https:", "ftp:", "ftps:", "sftp:"))


def make_absolute_url(url: str, base_url: str) -> str:
    if url.startswith("/") or not is_absolute_url(url):
        out = urljoin(base_url, url)
    else:
        out = url
    return out


def get_interesting_page_contents(
    url: str,
    verbose: bool = True,
    skip_details: bool = False,
) -> ScrapingResult:
    if verbose:
        print(f"Scraping: {url}")
    try:
        headers = headers_faking_navigator()
        page = requests.get(url, headers=headers)
    except Exception as e:
        return ScrapingResult(
            url=url,
            RESPONSE_CODE=0,
            VALID=False,
            exception=e,
        )

    out = {}
    out["url"] = url
    out["RESPONSE_CODE"] = page.status_code
    out["VALID"] = page.status_code == 200
    out["response_time"] = page.elapsed

    # Shortcut on images and stylesheets - or when details are not of interest
    if (
        url.endswith((".css", ".js", ".png", "jpg", ".jpeg", ".ico", ".svg"))
        or skip_details
    ):
        return ScrapingResult(
            **out,
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
        except KeyError:
            try:
                images.append(i["data-src"])
            except KeyError:
                pass
    out["images"] = images

    css_links = []
    for i in soup.find_all("link", rel="stylesheet"):
        try:
            css_link_i = make_absolute_url(i["href"], base_url=url)
            css_links.append(css_link_i)
        except KeyError:
            pass
    out["css_links"] = css_links

    script_links = []
    for i in soup.find_all("script", src=re.compile(".*")):
        try:
            script_i = make_absolute_url(i["src"], base_url=url)
            script_links.append(script_i)
        except KeyError:
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
        minimal_i = minimal_url(i)
        if current_domain in minimal_i:
            real_internal_links.append(minimal_i)
        else:
            real_external_links.append(minimal_i)

    out["emails"] = list_of_unique_elements(email_addresses)
    out["external_links"] = real_external_links
    out["internal_links"] = real_internal_links
    out["text_as_markdown"] = html_to_markdown(page.text)
    return ScrapingResult(**out)


def crawl_website(url: str, verbose: bool = True) -> dict[str, str]:
    crawled_internal_urls = []
    internal_urls_to_check = [url]
    crawled_external_urls = []
    external_urls_to_check = []

    res = dict()

    # Crawling internal links
    while len(internal_urls_to_check) > 0:
        url_i = internal_urls_to_check.pop(0)
        r_i = get_interesting_page_contents(url_i, verbose=verbose, skip_details=False)
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
        r_i = get_interesting_page_contents(url_i, verbose=verbose, skip_details=True)
        crawled_external_urls.append(url_i)
        ext_res[url_i] = r_i
    res["external"] = ext_res

    return res
