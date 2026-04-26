import requests

r = requests.delete("http://127.0.0.1:5000/api/bets/1")

print(r.json())
