import requests
import logging

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
        
        self.headers = {
            'Accept': 'text/html, image/avif, image/webp, image/apng, image/svg+xml, */*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US, en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Site': 'none',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
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

# Initialize the service
price_service = CryptoPriceService()
