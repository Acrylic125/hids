import requests

data = {
    'name': "d111",
    'password': "p1111"
}
base_url = "http://127.0.0.1:5000/"
response = requests.post(base_url + 'devices/auth', json=data)
print(response.json())

