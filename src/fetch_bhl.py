# src/fetch_bhl.py
from config import BHL_API_KEY
import requests

response = requests.get(
    "https://www.biodiversitylibrary.org/api3",
    params={"apikey": BHL_API_KEY, "op": "GetTitleMetadata", "format": "json"}
)