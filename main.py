import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# Basic functions
def list_of_unique_elements(x: list) -> list:
    return list(set(x))


def extract_email_address(x):
    return re.search(r"[\w\.-]+@[\w\.-]+[a-z]", x).group(0)


def extract_domain_from_url(url: str) -> str:
    return urlparse(url).netloc


def sentence_from_element(x: str) -> str:
    return " ".join(x.text.split())


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


def get_interesting_page_contents(url: str) -> ScrapingResult:
    print(f"Scraping: {url}")
    try:
        page = requests.get(url)
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
    if url.endswith((".png", "jpg", ".jpeg", ".css")):
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
            css_links.append(i["href"])
        except:
            pass
    out["css_links"] = css_links

    script_links = []
    for i in soup.find_all("script", src=re.compile(".*")):
        try:
            script_links.append(i["src"])
        except:
            pass
    out["script_links"] = script_links

    images_url = []
    for i in images:
        if i.startswith("data:image"):
            pass  # Skip processing embedded images
        elif is_absolute_url(i):
            images_url.append(i)
        else:
            images_url.append(urljoin(url, i))
    out["images_url"] = list_of_unique_elements(images_url)

    xs = soup.find_all("a", href=True)
    internal_links = []
    external_links = []
    email_addresses = []
    for p in xs:
        s_i = p["href"]
        if s_i.startswith("mailto:"):
            email_addresses.append(s_i.replace("mailto:", ""))
        elif is_absolute_url(s_i):
            external_links.append(s_i)
        else:
            local_link = urljoin(url, s_i)
            internal_links.append(local_link)

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


if __name__ == "__main__":
    target_website = "https://www.pierrevf.consulting"
    r = crawl_website(target_website)

    import pandas as pd

    internal_results = [v for i, v in r.items() if isinstance(v, ScrapingResult)]
    external_results = [v for i, v in r["external"].items()]
    target = ["INTERNAL"] * len(internal_results) + ["EXTERNAL"] * len(external_results)

    res = pd.DataFrame(
        data=dict(
            res=internal_results + external_results,
            target=target,
        )
    )

    res["url"] = res["res"].apply(lambda x: x.url)
    res["valid"] = res["res"].apply(lambda x: x.VALID)
    res["response_code"] = res["res"].apply(lambda x: x.RESPONSE_CODE)
    res["response_time_ms"] = res["res"].apply(
        lambda x: x.response_time / timedelta(milliseconds=1)
    )
    print(res)
