import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

def is_market_open():
    """
    Check if it's currently a trading day and trading hours
    """
    et_tz = pytz.timezone('US/Eastern')
    current_time = datetime.now(et_tz)
    
    # Check if it's weekend
    if current_time.weekday() >= 5:
        return False, "Market is closed (Weekend)"
    
    # Convert current time to hours and minutes in ET
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_time_float = current_hour + current_minute/60
    
    # Define market hours
    if 4 <= current_time_float < 9.5:
        return True, "Pre-market hours (4:00 AM - 9:30 AM ET)"
    elif 9.5 <= current_time_float < 16:
        return True, "Regular market hours (9:30 AM - 4:00 PM ET)"
    elif 16 <= current_time_float < 20:
        return True, "After-hours (4:00 PM - 8:00 PM ET)"
    else:
        return False, "Market is closed (Outside trading hours)"

def get_premarket_price(ticker_symbol):
    """
    Get pre-market price for a given stock ticker.
    """
    try:
        # Create ticker object
        ticker = yf.Ticker(ticker_symbol)
        
        # Get market data
        market_data = ticker.info
        
        result = {
            'Ticker': ticker_symbol,
            'Price': market_data.get('preMarketPrice'),
            'Regular Market Price': market_data.get('regularMarketPrice'),
            'Previous Close': market_data.get('previousClose')
        }
        
        # Calculate changes if we have the necessary data
        if result['Price'] and result['Previous Close']:
            result['Change'] = result['Price'] - result['Previous Close']
            result['Change%'] = (result['Change'] / result['Previous Close']) * 100
        else:
            result['Change'] = None
            result['Change%'] = None
            
        return result
        
    except Exception as e:
        return {
            'Ticker': ticker_symbol,
            'Price': None,
            'Regular Market Price': None,
            'Previous Close': None,
            'Change': None,
            'Change%': None
        }

def get_market_price(ticker_symbol):
    """
    Get regular market price for a given stock ticker.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period='2d')
        
        if not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
            change = current - prev
            change_percent = (change / prev) * 100
            
            return {
                'Ticker': ticker_symbol,
                'Price': current,
                'Change': change,
                'Change%': change_percent,
                'Volume': hist['Volume'].iloc[-1]
            }
    except Exception as e:
        return {
            'Ticker': ticker_symbol,
            'Price': None,
            'Change': None,
            'Change%': None,
            'Volume': None
        }

# Streamlit app
def main():
    st.title('Stock Market Dashboard')
    
    # Check market status
    is_open, market_status = is_market_open()
    st.info(f"Market Status: {market_status}")
    
    # Default tickers
    default_tickers = [
        'NVDA', 'AAPL', 'GOOGL', 'MSFT', 'META', 
        'TSLA', 'AMD', 'AMZN', 'NFLX', 'INTC',
        'SOUN', 'PLTR', 'AVGO', 'RGTI', 'IONQ'
    ]
    
    # Market type selection
    market_type = st.radio(
        "Select Market Type",
        ['market', 'pre_market'],
        horizontal=True
    )
    
    # Ticker input
    st.subheader('Add New Tickers')
    new_tickers = st.text_input(
        'Enter additional tickers (comma-separated)', 
        ''
    ).upper()
    
    # Combine default and new tickers
    all_tickers = default_tickers.copy()
    if new_tickers:
        additional_tickers = [t.strip() for t in new_tickers.split(',')]
        all_tickers.extend(additional_tickers)
    
    # Remove duplicates while preserving order
    all_tickers = list(dict.fromkeys(all_tickers))
    
    # Display current tickers
    st.subheader('Current Ticker List')
    st.write(', '.join(all_tickers))
    
    # Get and display data
    if st.button('Refresh Data'):
        with st.spinner('Fetching data...'):
            results = []
            
            for ticker in all_tickers:
                if market_type == 'pre_market':
                    data = get_premarket_price(ticker)
                else:
                    data = get_market_price(ticker)
                results.append(data)
            
            df = pd.DataFrame(results)
            
            # Format the dataframe
            for col in ['Price', 'Regular Market Price', 'Previous Close']:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: f'${x:.2f}' if isinstance(x, (int, float)) else 'N/A')
            
            if 'Change' in df.columns:
                df['Change'] = df['Change'].apply(lambda x: f'${x:+.2f}' if isinstance(x, (int, float)) else 'N/A')
            
            if 'Change%' in df.columns:
                df['Change%'] = df['Change%'].apply(lambda x: f'{x:+.2f}%' if isinstance(x, (int, float)) else 'N/A')
            
            if 'Volume' in df.columns:
                df['Volume'] = df['Volume'].apply(lambda x: f'{x:,.0f}' if isinstance(x, (int, float)) else 'N/A')
            
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime='text/csv'
            )

if __name__ == '__main__':
    main()
