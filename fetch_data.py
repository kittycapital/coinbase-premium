"""
Coinbase Bitcoin Premium Index - Data Fetcher
- Bitcoin price from CoinGecko
- Coinbase Premium calculated from Coinbase vs Binance prices
Premium accumulates over time (collected daily)
"""

import json
import requests
from datetime import datetime
import os

# Configuration
DATA_FILE = 'data.json'


def load_existing_data():
    """Load existing data.json to preserve accumulated premium history"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return None


def fetch_bitcoin_price():
    """Fetch 12 months of daily Bitcoin price from CoinGecko"""
    
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    params = {
        'vs_currency': 'usd',
        'days': 365,
        'interval': 'daily'
    }
    
    print("📡 Fetching BTC price from CoinGecko (12 months)...")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        prices_by_date = {}
        
        for item in data['prices']:
            timestamp = item[0] / 1000
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            price = item[1]
            prices_by_date[date] = round(price, 2)
        
        print(f"   ✅ Got {len(prices_by_date)} days of price data")
        return prices_by_date
        
    except Exception as e:
        print(f"   ❌ Error fetching BTC price: {e}")
        return {}


def fetch_coinbase_price():
    """Fetch current BTC price from Coinbase"""
    
    print("\n📡 Fetching Coinbase BTC price...")
    
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        price = float(data['data']['amount'])
        print(f"   ✅ Coinbase BTC: ${price:,.2f}")
        return price
        
    except Exception as e:
        print(f"   ❌ Error fetching Coinbase price: {e}")
        return None


def fetch_binance_price():
    """Fetch current BTC price from Binance"""
    
    print("\n📡 Fetching Binance BTC price...")
    
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {'symbol': 'BTCUSDT'}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        price = float(data['price'])
        print(f"   ✅ Binance BTC: ${price:,.2f}")
        return price
        
    except Exception as e:
        print(f"   ❌ Error fetching Binance price: {e}")
        return None


def calculate_premium(coinbase_price, binance_price):
    """Calculate Coinbase Premium Index"""
    
    if coinbase_price is None or binance_price is None:
        return None
    
    if binance_price == 0:
        return None
    
    # Premium = (Coinbase - Binance) / Binance * 100
    premium = ((coinbase_price - binance_price) / binance_price) * 100
    
    print(f"\n📊 Coinbase Premium: {premium:+.4f}%")
    
    return round(premium, 4)


def update_premium_history(existing_data, today_premium):
    """Update premium history with today's value"""
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get existing premium history or start fresh
    if existing_data and 'premium_dates' in existing_data and 'premium_index' in existing_data:
        premium_dates = existing_data['premium_dates']
        premium_values = existing_data['premium_index']
    else:
        premium_dates = []
        premium_values = []
    
    # Add today's value if we have it
    if today_premium is not None:
        if today not in premium_dates:
            premium_dates.append(today)
            premium_values.append(today_premium)
            print(f"\n📈 Added premium for {today}: {today_premium:+.4f}%")
        else:
            # Update today's value
            idx = premium_dates.index(today)
            premium_values[idx] = today_premium
            print(f"\n📈 Updated premium for {today}: {today_premium:+.4f}%")
    
    # Keep only last 365 days
    if len(premium_dates) > 365:
        premium_dates = premium_dates[-365:]
        premium_values = premium_values[-365:]
    
    return premium_dates, premium_values


def main():
    print("🚀 Starting Coinbase Premium Index data fetch...\n")
    
    # Load existing data (to preserve premium history)
    existing_data = load_existing_data()
    
    # Fetch Bitcoin price for chart
    btc_prices = fetch_bitcoin_price()
    
    if not btc_prices:
        print("❌ Error: Could not fetch Bitcoin price")
        return
    
    # Fetch current prices from both exchanges
    coinbase_price = fetch_coinbase_price()
    binance_price = fetch_binance_price()
    
    # Calculate premium
    today_premium = calculate_premium(coinbase_price, binance_price)
    
    # Update premium history
    premium_dates, premium_values = update_premium_history(existing_data, today_premium)
    print(f"   ✅ Premium history: {len(premium_dates)} data points")
    
    # Prepare dates and prices arrays
    dates = sorted(btc_prices.keys())
    prices = [btc_prices[d] for d in dates]
    
    # Save to JSON
    output = {
        'dates': dates,
        'btc_prices': prices,
        'premium_dates': premium_dates,
        'premium_index': premium_values,
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }
    
    with open(DATA_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved to {DATA_FILE}")
    print(f"   📅 BTC date range: {dates[0]} to {dates[-1]}")
    print(f"   💰 Latest BTC: ${prices[-1]:,.0f}")
    
    if premium_values:
        print(f"   📊 Latest Premium: {premium_values[-1]:+.4f}%")
    else:
        print(f"   📊 Latest Premium: N/A")


if __name__ == '__main__':
    main()
