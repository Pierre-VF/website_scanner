import socket
import ssl
from typing import Any
from urllib.parse import urlparse

import requests


class SecurityError(RuntimeError):
    pass


def _hostname_from_url_or_hostname(x: str) -> str:
    if x.startswith("https://") or x.startswith("http://"):
        out = urlparse(x).netloc
    else:
        out = x
    return out


def allows_insecure_connections(hostname: str) -> tuple[bool, Any]:
    hostname = _hostname_from_url_or_hostname(hostname)
    with requests.Session() as s:
        try:
            insecure_url = f"http://{hostname}/"
            insecure_result = s.get(insecure_url)
            fails_on_insecure = False
        except Exception as e:
            fails_on_insecure = True
            insecure_result = None

        try:
            secure_url = f"https://{hostname}/"
            secure_result = s.get(secure_url)
            fails_on_secure = False
        except Exception as e:
            fails_on_secure = True
            secure_result = None

    details = {
        "fails_on_http": fails_on_insecure,
        "fails_on_https": fails_on_secure,
        "response_on_http": insecure_result,
        "response_on_https": secure_result,
    }

    return not fails_on_insecure, details


def get_tls_version(hostname: str, raise_if_unsafe: bool = True) -> str:
    """Returns the TLS version used by a website

    :param hostname: URL of the website to check
    :return: TLS version
    """
    hostname = _hostname_from_url_or_hostname(hostname)
    context = ssl.create_default_context()

    with socket.create_connection((hostname, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            tls_version = ssock.version()

    if raise_if_unsafe:
        check_tls_version(tls_version)

    return tls_version


def check_tls_version(tls_version: str) -> None:
    if tls_version in ["TLSv1.0", "TLSv1.1"]:
        raise SecurityError(
            f"TLS protocol used ({tls_version}) is no longer considered secure"
        )
