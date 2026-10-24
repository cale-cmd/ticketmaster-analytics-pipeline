import requests

url = "https://app.ticketmaster.com/discovery/v2/events.json"

params = {
    "apikey" : "xoKbSpr9TzICBgLtz34MF89Y7IB55vkP",
    "city" : "New York",
    "segment" : "Music",
    "size" : 1
}

response = requests.get(url , params=params)

data = response.json()

print(type(data["_embedded"]["events"][0]))
print(data["_embedded"]["events"][0].keys())