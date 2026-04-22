import requests

pick = {
        "user_id": "1",
        "symbol": "AAPL", 
        }

test = requests.post("http://127.0.0.1:5000/api/stockpicks", json=pick)
print(test.json())

"""
change = {
        'title': 'Changed Title'
        }

test = requests.patch("http://127.0.0.1:5000/api/predictions/1", json=change)

print(test.json())


test = requests.delete("http://127.0.0.1:5000/api/predictions/1")

print(test.json())

"""
