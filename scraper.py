import requests
from websocket import create_connection
import re

class TradingViewScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.auth_token = None

    def get_auth_token(self):
        sign_in_url = 'https://www.tradingview.com/accounts/signin/'
        data = {"username": self.username, "password": self.password, "remember": "on"}
        headers = {'Referer': 'https://www.tradingview.com'}
        response = requests.post(url=sign_in_url, data=data, headers=headers)
        if response.status_code == 200 and 'user' in response.json():
            self.auth_token = response.json()['user']['auth_token']
        else:
            raise Exception("Failed to retrieve auth token.")

    def fetch_data(self, chart_id="BTCUSD"):
        if not self.auth_token:
            raise Exception("Auth token not available. Please login first.")
        headers = {'Authorization': f"Bearer {self.auth_token}"}
        ws = create_connection(f'wss://data.tradingview.com/socket.io/websocket?from=chart/{chart_id}/&date=XXXX_XX_XX')
        response = ws.recv()
        return response  # Parse and use data as needed