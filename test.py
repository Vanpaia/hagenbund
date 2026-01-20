import requests

"""
# Finnhub
API_KEY = "d5n1h3pr01qj2afiodfgd5n1h3pr01qj2afiodg0"
keyword = "BAE Systems"
request_url = f"https://finnhub.io/api/v1/search?q={keyword}&exchange=US&token={API_KEY}"

response = requests.get(request_url)

print(response.json())


# Alpha Vantage
API_KEY = "EZZFWNSYKG53Z4BK"
keyword = "BAE+Systems"
url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={keyword}&apikey={API_KEY}'

r = requests.get(url)
data = r.json()

print(data)

"""
# FMB
API_KEY = "HbV6HuiymhhFdxedKavfR23SVTW9ifO1"
header = {"apikey":API_KEY}
keyword = "Rheinmetall"
search_url = f'https://financialmodelingprep.com/stable/search-name?query={keyword}'
r = requests.get(search_url, headers=header)
data = r.json()

print(data)

symbol = data[0]["symbol"]
info_url = f'https://financialmodelingprep.com/stable/profile?symbol={symbol}'
r = requests.get(info_url, headers=header)

data = r.json()

print(data)
