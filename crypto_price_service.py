import requests
import logging
from dotenv import load_dotenv
import os
load_dotenv()
import os
import requests
import logging

class CryptoPriceService:
    def __init__(self):
        # API Key for CoinStats
        self.api_key = os.getenv("COINSTATS_API_KEY")
        
        # Mapping of tokens to their symbols used in CoinStats
        self.token_map = {
            'rndr': 'render-token',
            'bst': 'blocksquare',
            'ybr': 'yieldbricks',
            'rio': 'realio-network',
            'props': 'propbase',
        }
        
        self.headers = {"accept": "application/json",
                        "X-API-KEY": self.api_key}


    def get_current_price(self, token_name: str) -> float:
        """
        Fetch current price from CoinStats API.
        Args:
            token_name (str): Internal token name (e.g., rndr, bst).
        Returns:
            float: Current price of the token or 0.0 if not found.
        """
        token_symbol = self.token_map.get(token_name)
        if not token_symbol:
            logging.error(f"Token {token_name} not found in token map.")
            return 0.0

        try:
            response = requests.get(
                f"https://openapiv1.coinstats.app/coins/{token_symbol}",
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()
            # CoinStats returns prices under 'price' key
            price = data.get("price", 0.0)

            logging.info(f"Price for {token_name}: {price}")
            return float(price)

        except requests.RequestException as e:
            logging.error(f"Request error for {token_name}: {e}")
            return 0.0
        except Exception as e:
            logging.error(f"Unexpected error for {token_name}: {e}")
            return 0.0

class CryptoComparePriceService:
    def __init__(self):
        """
        Initialize the CryptoComparePriceService with the API key.
        Args:
            api_key (str): Your CryptoCompare API key.
        """
        self.api_key =  os.getenv("CRYPTOCOMPARE_API_KEY")
        # Mapping of tokens to their CryptoCompare symbols
        self.token_map = {
            'rndr': 'render-token',
            'bst': 'blocksquare',
            'ybr': 'yieldbricks',
            'rio': 'realio-network',
            'props': 'propbase',
        }
        
        self.base_url = "https://min-api.cryptocompare.com/data/price"
        self.headers = {"accept": "application/json",
                    "X-API-KEY": "C42yBtNcADD21l7dcxJaUiEAbGblxL0B7Naugp5rEBM="}

    def get_current_price(self, token_name: str) -> float:
        """
        Fetch current price from CryptoCompare API.
        Args:
            token_name (str): Internal token name (e.g., rndr, bst).
        Returns:
            float: Current price of the token in USD or 0.0 if not found.
        """
        token_symbol = self.token_map.get(token_name)
        if not token_symbol:
            logging.error(f"Token {token_name} not found in token map.")
            return 0.0

        try:
            response = requests.get(
                self.base_url,
                params={"fsym": token_symbol, "tsyms": "USD"},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            price = data.get('price', 0.0)
            
            logging.info(f"Price for {token_name} ({token_symbol}): {price}")
            return float(price)

        except requests.RequestException as e:
            logging.error(f"Request error for {token_name}: {e}")
            return 0.0
        except Exception as e:
            logging.error(f"Unexpected error for {token_name}: {e}")
            return 0.0
# Initialize the service
price_service = CryptoPriceService()
