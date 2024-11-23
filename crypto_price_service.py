import requests


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

        headers = {
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
        token_id = self.token_map.get(token_name)
        if not token_id:
            print(f"Token {token_name} not found in token map.")
            return 0.0

        try:
           
            response = requests.get("https://api.coingecko.com/api/v3/simple/price",headers={headers},
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
