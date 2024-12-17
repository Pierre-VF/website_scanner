import pprint

import typer

from pvfs_website_scanner.runner import check_target_website

app = typer.Typer()


@app.command()
def check(url: str):
    """
    Checks a website for broken links and configuration issues.
    """
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(f"==== Checking website: {url} ====")
    res = check_target_website(url, verbose=True)
    pp.pprint(res)
    pp.pprint("======== Check completed ========")


if __name__ == "__main__":
    check(url="https://pierrevf.consulting/")
