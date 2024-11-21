from typing import Dict, Optional
import requests
import time
from datetime import datetime
import threading
import logging

class TokenPriceCache:
    def __init__(self, cache_duration_seconds: int = 60):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = cache_duration_seconds
        self.lock = threading.Lock()
        self.token_map = {
            'Bitcoin': 'bitcoin',
            'Ethereum': 'ethereum',
            'Ripple': 'ripple'
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _is_cache_valid(self, token: str) -> bool:
        """Check if the cached price for a token is still valid"""
        if token not in self.cache:
            return False
        
        current_time = time.time()
        last_update_time = self.cache[token]['timestamp']
        
        return (current_time - last_update_time) < self.cache_duration
    
    def _fetch_price(self, token_name: str) -> Optional[float]:
        """Fetch current price from CoinGecko API"""
        try:
            token_id = self.token_map.get(token_name, token_name.lower())
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
            
            self.logger.error(f"Failed to fetch price for {token_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching price for {token_name}: {str(e)}")
            return None
    
    def get_token_price(self, token_name: str) -> Dict:
        """Get token price from cache or fetch if needed"""
        with self.lock:
            # Check cache first
            if self._is_cache_valid(token_name):
                cache_data = self.cache[token_name]
                return {
                    'price': cache_data['price'],
                    'last_updated': cache_data['last_updated'],
                    'source': 'cache'
                }
            
            # Fetch new price
            current_price = self._fetch_price(token_name)
            
            if current_price is not None:
                # Update cache
                self.cache[token_name] = {
                    'price': current_price,
                    'timestamp': time.time(),
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                return {
                    'price': current_price,
                    'last_updated': self.cache[token_name]['last_updated'],
                    'source': 'api'
                }
            
            # Return last cached price if fetch failed
            if token_name in self.cache:
                cache_data = self.cache[token_name]
                return {
                    'price': cache_data['price'],
                    'last_updated': cache_data['last_updated'],
                    'source': 'stale_cache'
                }
            
            return {
                'price': 0,
                'last_updated': None,
                'source': 'error'
            }
    
    def calculate_holdings(self, token_name: str, tokens_held: float) -> Dict:
        """Calculate current holdings value using cached price"""
        price_data = self.get_token_price(token_name)
        current_price = price_data['price']
        
        return {
            'token_name': token_name,
            'current_price': current_price,
            'tokens_held': tokens_held,
            'total_value': current_price * tokens_held,
            'last_updated': price_data['last_updated'],
            'data_source': price_data['source']
        }

# Initialize global price cache
price_cache = TokenPriceCache(cache_duration_seconds=60)