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
        token_id = self.token_map.get(token_name)
        if not token_id:
            print(f"Token {token_name} not found in token map.")
            return 0.0

        try:
            # Use CoinGecko's simple price API
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",headers=headers,
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
