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
    res = check_target_website(url, verbose=False)
    pp.pprint(res)


if __name__ == "__main__":
    app()
