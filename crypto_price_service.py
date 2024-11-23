import requests
import random

class CryptoPriceService:
    def __init__(self):
        # Mapping of tokens to their CoinGecko IDs
        self.token_map = {
            'rndr': 'render-token',
            'bst': 'blocksquare',
            'ybr': 'yieldbricks',
            'rio': 'realio-network',
            'props': 'propbase',
        }

    def get_current_price(self, token_name: str) -> float:
        """
        Fetch current price from CoinGecko API.
        Args:
            token_name (str): Internal token name (e.g., rndr, bst).
        Returns:
            float: Current price of the token or 0.0 if not found.
        """

        UserAgents=['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36']

        token_id = self.token_map.get(token_name)
        if not token_id:
            print(f"Token {token_name} not found in token map.")
            return 0.0

        try:
           
            response = requests.get("https://api.coingecko.com/api/v3/simple/price",headers={'User-Agent':  random.choice(UserAgents)},
                params={"ids": token_id, "vs_currencies": "usd"}
            )
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()

            # Extract the price
            return data.get(token_id, {}).get("usd", 0.0)
        except Exception as e:
            print(f"Error retrieving price for {token_name}: {str(e)}")
            return 0.0

# Initialize the service
price_service = CryptoPriceService()
