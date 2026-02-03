import requests

API_KEY = "AIzaSyCrwzc0nLMqGChnhYjG0iDOn0MFsENKASQ"
SEARCH_ENGINE_ID = "77df10be511d24618"

url = "https://www.googleapis.com/customsearch/v1"
params = {
    'q': "cat", 
    'cx': SEARCH_ENGINE_ID,
    'key': API_KEY,
    'searchType': 'image',
    'num': 1
}

print("Testing connection...")
response = requests.get(url, params=params)

print(f"Status Code: {response.status_code}")
print("--- FULL ERROR MESSAGE ---")
print(response.text) # This is the secret clue we need!