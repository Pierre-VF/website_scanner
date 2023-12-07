from datetime import timedelta

try:
    from .src import cookies, crawler, security
except:
    from src import cookies, crawler, security


if __name__ == "__main__":
    import pandas as pd

    target_website = "https://dtechtive.com/"
    # target_website = "https://www.pierrevf.consulting/"

    tls_version = security.get_tls_version(target_website, raise_if_unsafe=True)
    allows_insecure, details = security.allows_insecure_connections(target_website)
    uses_cookies, cookies_details = cookies.page_uses_cookies(target_website)

    r = crawler.crawl_website(target_website)

    internal_results = [
        v for i, v in r.items() if isinstance(v, crawler.ScrapingResult)
    ]
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
