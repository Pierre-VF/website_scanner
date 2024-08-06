from datetime import timedelta

import pandas as pd

from . import cookies, crawler, security


def check_target_website(url: str, verbose: bool = True) -> dict[str, pd.DataFrame]:
    target_website = url

    tls_version = security.get_tls_version(target_website, raise_if_unsafe=True)
    allows_insecure, details = security.allows_insecure_connections(target_website)
    uses_cookies, cookies_details = cookies.page_uses_cookies(target_website)

    r = crawler.crawl_website(target_website, verbose=verbose)

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

    df_invalid_internal = res[(res["valid"] == False) & (res["target"] == "INTERNAL")]
    df_invalid_external = res[(res["valid"] == False) & (res["target"] == "EXTERNAL")]

    if verbose:
        print(res)

        print("/ ---------------------------------------------------")
        print("/ ---------------------------------------------------")
        print(f"{len(df_invalid_internal)} invalid internal links:")
        print(df_invalid_internal)
        print("URLs:")
        df_invalid_internal["url"].apply(print)
        print(" ")
        print("/ ---------------------------------------------------")
        print("/ ---------------------------------------------------")
        print(f"{len(df_invalid_external)} invalid external links:")
        print(df_invalid_external)
        print("URLs:")
        df_invalid_external["url"].apply(print)

    return {
        "tls_version": tls_version,
        "uses_cookies": uses_cookies,
        "allows_insecure_connection": allows_insecure,
        "all": res,
        "invalid_internal_urls": df_invalid_internal,
        "invalid_external_urls": df_invalid_external,
    }
