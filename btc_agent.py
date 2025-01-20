import requests
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(override=True)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_EMAIL = os.getenv("SUPABASE_EMAIL")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")

if not all([SUPABASE_URL, SUPABASE_KEY, SUPABASE_EMAIL, SUPABASE_PASSWORD]):
    raise ValueError("Missing Supabase credentials. Please check your .env file.")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Authenticate with Supabase
def authenticate():
    try:
        response = supabase.auth.sign_in_with_password({
            "email": SUPABASE_EMAIL,
            "password": SUPABASE_PASSWORD
        })
        print("Successfully authenticated with Supabase")
        return True
    except Exception as e:
        print(f"Authentication error: {e}")
        return False

def get_btc_price():
    """
    Fetches the current Bitcoin price in USD using the CoinGecko API.
    
    Returns:
        float: Current Bitcoin price in USD
        None: If there's an error fetching the price
    """
    try:
        # CoinGecko API endpoint for Bitcoin price
        url = "https://api.coingecko.com/api/v3/simple/price"
        
        # Parameters for the API request
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd"
        }
        
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Extract the price from the response
        data = response.json()
        btc_price = data["bitcoin"]["usd"]
        
        return btc_price
    
    except requests.RequestException as e:
        print(f"Error fetching Bitcoin price: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing Bitcoin price data: {e}")
        return None

def store_btc_price(price):
    """
    Stores the Bitcoin price in Supabase database.
    
    Args:
        price (float): Bitcoin price to store
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = {
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Insert into Supabase
        result = supabase.table('btc_price').insert(data).execute()
        print(f"Successfully stored BTC price: ${price:,.2f}")
        return True
        
    except Exception as e:
        print(f"Error storing price in database: {e}")
        return False

# Example usage
if __name__ == "__main__":
    if authenticate():
        price = get_btc_price()
        if price:
            print(f"Current Bitcoin price: ${price:,.2f} USD")
            store_btc_price(price)
        else:
            print("Failed to fetch Bitcoin price")
    else:
        print("Failed to authenticate with Supabase")
