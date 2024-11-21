import requests
from datetime import datetime
import time
from functools import lru_cache

class CryptoPriceService:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.token_map = {
            'Bitcoin': 'bitcoin',
            'Ethereum': 'ethereum',
            'Ripple': 'ripple'
        }
        
    @lru_cache(maxsize=100)
    def get_cached_price(self, token_name: str, timestamp: int) -> float:
        """Cache prices for 1 minute using the timestamp as part of the cache key"""
        return self.get_current_price(token_name)
    
    def get_current_price(self, token_name: str) -> float:
        """
        Get the current price of a token in USD
        Returns the price or None if the token is not found
        """
        try:
            # Get the coingecko token id
            token_id = self.token_map.get(token_name.lower(), token_name.lower())
            
            # Make API request
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={
                    "ids": token_id,
                    "vs_currencies": "usd"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if token_id in data:
                    return data[token_id]["usd"]
            
            return None
            
        except Exception as e:
            print(f"Error fetching price for {token_name}: {str(e)}")
            return None
    
    def get_current_holdings_value(self, token_name: str, tokens_held: float) -> dict:
        """
        Calculate the current value of holdings
        Returns a dictionary with current price and total value
        """
        # Get current minute timestamp for caching
        cache_timestamp = int(time.time() / 60)
        
        # Get cached price
        current_price = self.get_cached_price(token_name, cache_timestamp)
        
        if current_price is not None:
            total_value = current_price * tokens_held
            return {
                "current_price": current_price,
                "total_value": total_value,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {
                "current_price": 0,
                "total_value": 0,
                "last_updated": None,
                "error": "Could not fetch current price"
            }

# Initialize the service
price_service = CryptoPriceService()