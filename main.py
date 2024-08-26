import pprint

import typer

try:
    from src.runner import check_target_website
except ImportError:
    pass

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
    app()
