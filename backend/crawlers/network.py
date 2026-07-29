import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_retry_session():
    retries = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session
