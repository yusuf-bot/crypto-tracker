import requests
import logging
from dotenv import load_dotenv
import os
load_dotenv()
class CryptoPriceService:
    def __init__(self):
        # Mapping of tokens to their CoinGecko IDs
        self.api_key=os.getenv("COINGECKO_API_KEY")
        self.token_map = {
            'rndr': 'render-token',
            'bst': 'blocksquare',
            'ybr': 'yieldbricks',
            'rio': 'realio-network',
            'props': 'propbase',
        }
        
        self.headers = {
            'Authorization': f'Apikey {self.api_key}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        }

    def get_current_price(self, token_name: str) -> float:
        """
        Fetch current price from CoinGecko API.
        Args:
            token_name (str): Internal token name (e.g., rndr, bst).
        Returns:
            float: Current price of the token or 0.0 if not found.
        """


        token_id = self.token_map.get(token_name)
        if not token_id:
            logging.error(f"Token {token_name} not found in token map.")
            return 0.0

        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": token_id, "vs_currencies": "usd"},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            price = data.get(token_id, {}).get('usd', 0.0)
            
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
            'rndr': 'RNDR',
            'bst': 'BST',
            'ybr': 'YBR',
            'rio': 'RIO',
            'props': 'PROPS',
        }
        
        self.base_url = "https://min-api.cryptocompare.com/data/price"
        self.headers = {
            'Authorization': f'Apikey {self.api_key}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        }

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
            price = data.get('USD', 0.0)
            
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
