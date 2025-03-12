from flask import Flask, request, render_template_string
import os
import requests
import time
import base64
import json

app = Flask(__name__)

# Load your credentials from Replit secrets
EBAY_CLIENT_ID = os.environ["EBAY_CLIENT_ID"]
EBAY_CLIENT_SECRET = os.environ["EBAY_CLIENT_SECRET"]

# Global variables to store the current access token and its expiry time
current_access_token = None
token_expiry_time = None

def get_ebay_access_token(client_id, client_secret):
    # Encode client_id and client_secret
    credentials = f"{client_id}:{client_secret}".encode()
    encoded_credentials = base64.b64encode(credentials).decode('utf-8')

    url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    body = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"  # Using only the basic scope
    }

    response = requests.post(url, headers=headers, data=body)
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info["access_token"]
        expires_in = token_info["expires_in"]  # Time in seconds until the token expires

        # Calculate the expiry time as current time + expires_in
        expiry_time = time.time() + expires_in

        return access_token, expiry_time
    else:
        print(f"Failed to obtain token: {response.status_code}, {response.text}")
        return None, None

# Function to check if the token is expired and refresh it if needed
def get_valid_access_token():
    global current_access_token, token_expiry_time

    if not current_access_token or time.time() >= token_expiry_time:
        current_access_token, token_expiry_time = get_ebay_access_token(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)

    return current_access_token

def search_items(access_token, keywords, category_id=None, min_price=None, max_price=None, item_condition=None):
  url = "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"  # Sandbox endpoint for Finding API
  headers = {
      "X-EBAY-SOA-SECURITY-APPNAME": EBAY_CLIENT_ID,  # Use your Client ID
      "Content-Type": "application/json",
  }
  params = {
      "OPERATION-NAME": "findItemsByKeywords",
      "SERVICE-VERSION": "1.0.0",
      "RESPONSE-DATA-FORMAT": "JSON",
      "REST-PAYLOAD": "",
      "keywords": keywords,
      # Add additional parameters based on your criteria, like category, price, condition
  }

  # Add optional parameters
  if category_id:
      params["categoryId"] = category_id
  if min_price:
      params["itemFilter(0).name"] = "MinPrice"
      params["itemFilter(0).value"] = min_price
  if max_price:
      params["itemFilter(1).name"] = "MaxPrice"
      params["itemFilter(1).value"] = max_price
  if item_condition:
      params["itemFilter(2).name"] = "Condition"
      params["itemFilter(2).value"] = item_condition

  response = requests.get(url, headers=headers, params=params)
  if response.status_code == 200:
      return json.loads(response.text)
  else:
      print(f"Failed to search items: {response.status_code}, {response.text}")
      return None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keywords = request.form.get('keywords')
        category_id = request.form.get('category_id')
        min_price = request.form.get('min_price')
        max_price = request.form.get('max_price')
        item_condition = request.form.get('item_condition')

        access_token = get_valid_access_token()
        if access_token:
            results = search_items(access_token, keywords, category_id, min_price, max_price, item_condition)
            return render_template_string("""
                <h1>Search Results</h1>
                <a href="/">New Search</a>
                <pre>{{ results }}</pre>
                """, results=json.dumps(results, indent=4))
        else:
            return "Failed to obtain access token."

    return '''
    <form method="POST">
        Keywords: <input type="text" name="keywords"><br>
        Category ID: <input type="text" name="category_id"><br>
        Min Price: <input type="text" name="min_price"><br>
        Max Price: <input type="text" name="max_price"><br>
        Item Condition: <input type="text" name="item_condition"><br>
        <input type="submit" value="Search">
    </form>
    '''

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)

