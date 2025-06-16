import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from db_operations import (
    get_or_create_stock,
    save_stock_prices,
    get_stock_prices
)

def get_usd_to_inr():
    """
    Fetch real-time USD to INR exchange rate using Yahoo Finance
    """
    try:
        ticker = yf.Ticker("USDINR=X")
        df = ticker.history(period="1d")
        return float(df['Close'].iloc[-1])
    except Exception as e:
        print(f"Error fetching USD to INR rate: {e}")
        return 83.0  # fallback

def format_inr(value):
    """
    Format INR value into Indian-readable string (Cr/Lakh)
    """
    try:
        if value >= 1e7:
            return f"₹{value / 1e7:.2f} Cr"
        elif value >= 1e5:
            return f"₹{value / 1e5:.2f} L"
        else:
            return f"₹{value:.2f}"
    except:
        return f"₹{value}"

def get_stock_data(symbol, start_date, end_date):
    """
    Fetch stock data from Yahoo Finance and save to database
    """
    try:
        db_data = get_stock_prices(symbol, start_date, end_date)
        if db_data is not None and not db_data.empty and len(db_data) >= (end_date - start_date).days * 0.7:
            print(f"Using cached data for {symbol} from database")
            return db_data

        print(f"Fetching fresh data for {symbol} from Yahoo Finance")
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')

        info = stock.info
        usd_to_inr = get_usd_to_inr()

        get_or_create_stock(
            symbol=symbol,
            name=info.get('shortName', symbol),
            sector=info.get('sector'),
            industry=info.get('industry'),
            description=info.get('longBusinessSummary'),
            market_cap=int(info.get('marketCap', 0) * usd_to_inr)
        )

        save_stock_prices(symbol, df)
        return df

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        current_date = datetime.datetime.now()
        dates = [current_date - datetime.timedelta(days=i) for i in range(30)]
        df = pd.DataFrame({
            'Date': dates,
            'Open': [np.nan] * 30,
            'High': [np.nan] * 30,
            'Low': [np.nan] * 30,
            'Close': [np.nan] * 30,
            'Volume': [np.nan] * 30
        })
        df = df.set_index('Date')
        return df

def get_company_info(symbol):
    """
    Get company information for a given stock symbol
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        usd_to_inr = get_usd_to_inr()

        company_info = {
            'name': info.get('shortName', 'Unknown'),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'description': info.get('longBusinessSummary', 'No description available.'),
            'market_cap': format_inr(info.get('marketCap', 0) * usd_to_inr),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'revenue': format_inr(info.get('totalRevenue', 0) * usd_to_inr),
            'eps': format_inr(info.get('trailingEps', 0) * usd_to_inr)
        }

        get_or_create_stock(
            symbol=symbol,
            name=company_info['name'],
            sector=company_info['sector'],
            industry=company_info['industry'],
            description=company_info['description'],
            market_cap=int(info.get('marketCap', 0) * usd_to_inr)
        )

        return company_info

    except Exception as e:
        print(f"Error fetching company info for {symbol}: {e}")
        return {
            'name': symbol,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'description': 'Information not available.',
            'market_cap': '₹0',
            'pe_ratio': 0,
            'dividend_yield': 0,
            'revenue': '₹0',
            'eps': '₹0'
        }

def get_popular_stocks():
    return [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corp.'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corp.'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'}
    ]

def search_stocks(query):
    all_stocks = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.',
        'GOOG': 'Alphabet Inc. (Class C)',
        'AMZN': 'Amazon.com Inc.',
        'TSLA': 'Tesla Inc.',
        'META': 'Meta Platforms Inc.',
        'NVDA': 'NVIDIA Corporation',
        'BRK-B': 'Berkshire Hathaway Inc.',
        'JPM': 'JPMorgan Chase & Co.',
        'JNJ': 'Johnson & Johnson',
        'V': 'Visa Inc.',
        'PG': 'Procter & Gamble Co.',
        'UNH': 'UnitedHealth Group Inc.',
        'HD': 'Home Depot Inc.',
        'BAC': 'Bank of America Corp.',
        'MA': 'Mastercard Inc.',
        'XOM': 'Exxon Mobil Corporation',
        'DIS': 'Walt Disney Co.',
        'NFLX': 'Netflix Inc.',
        'PYPL': 'PayPal Holdings Inc.',
        'INTC': 'Intel Corporation',
        'CSCO': 'Cisco Systems Inc.',
        'VZ': 'Verizon Communications Inc.',
        'ADBE': 'Adobe Inc.',
        'PFE': 'Pfizer Inc.',
        'CRM': 'Salesforce Inc.',
        'CMCSA': 'Comcast Corporation',
        'KO': 'Coca-Cola Co.',
        'PEP': 'PepsiCo Inc.'
    }

    query = query.upper()
    return [
        {'symbol': symbol, 'name': name}
        for symbol, name in all_stocks.items()
        if query in symbol or query in name.upper()
    ][:10]
