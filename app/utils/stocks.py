import requests
from config import Config

API_KEY = Config.FMP_API

def search_stock_ticker(keywords):

    header = {"apikey":API_KEY}
    url = f'https://financialmodelingprep.com/stable/search-name?query={keywords}'
    r = requests.get(url, headers=header)

    if r.ok:
        data = r.json()
        return data

def get_stock_info(symbol):
    header = {"apikey":API_KEY}
    url = f'https://financialmodelingprep.com/stable/profile?symbol={symbol}'
    r = requests.get(url, headers=header)

    if r.ok:
        data = r.json()
        return data

