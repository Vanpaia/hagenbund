import requests

prediction = {
        "user_id": "1",
        "title": "Test2",
        "description": "This is the description for the 2nd test.",
        "category": "ENT", 
        }

test = requests.post("http://127.0.0.1:5000/api/predictions", json=prediction)
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
