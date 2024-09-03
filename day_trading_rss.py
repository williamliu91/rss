import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import feedparser

# Function to fetch data based on the selected period and stock symbol
def fetch_data(stock_symbol, interval, yf_period):
    try:
        data = yf.download(stock_symbol, period=yf_period, interval=interval)
        if data.empty:
            st.error(f"No data returned for ticker {stock_symbol}. Please check the ticker symbol or interval.")
        return data
    except Exception as e:
        st.error(f"Error fetching data from Yahoo Finance: {e}")
        return pd.DataFrame()  # Return empty DataFrame

# Function to calculate support and resistance levels
def calculate_support_resistance(data, window=20):
    if 'Low' not in data.columns or 'High' not in data.columns:
        st.error("Data does not contain required columns for support and resistance calculation.")
        return None, None

    if len(data) < window:
        st.error("Not enough data to calculate support and resistance.")
        return None, None

    try:
        data['Support'] = data['Low'].rolling(window=window).min()
        data['Resistance'] = data['High'].rolling(window=window).max()

        latest_support = data['Support'].dropna().iloc[-1] if not data['Support'].dropna().empty else None
        latest_resistance = data['Resistance'].dropna().iloc[-1] if not data['Resistance'].dropna().empty else None

        if latest_support is None or latest_resistance is None:
            st.error("Failed to retrieve latest support or resistance values.")
        
        return latest_support, latest_resistance
    except Exception as e:
        st.error(f"Error calculating support and resistance: {e}")
        return None, None

# Function to fetch stock news using RSS feed
def fetch_stock_news(stock_symbol):
    url = "https://finance.yahoo.com/rss/headline?s=" + stock_symbol
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries:
            articles.append({
                'title': entry.title,
                'publishedAt': entry.published,
                'url': entry.link
            })
        return articles
    except Exception as e:
        st.error(f"Error fetching news from RSS feed: {e}")
        return []

# Streamlit app
def main():
    st.title("Stock Analysis with News")

    # Sidebar for user input
    st.sidebar.header("Settings")
    stock_symbols = [
        "AAPL",  # Apple
        "GOOGL",  # Alphabet (Google)
        "MSFT",  # Microsoft
        "AMZN",  # Amazon
        "TSLA",  # Tesla
        "META",  # Meta Platforms (Facebook)
        "NFLX",  # Netflix
        "NVDA",  # NVIDIA
        "INTC",  # Intel
        "AMD"    # AMD
    ]
    stock_symbol = st.sidebar.selectbox("Select Stock Symbol", stock_symbols)
    
    # Adding a new dropdown for interval selection
    interval = st.sidebar.selectbox(
        "Select Interval", 
        ["1m", "5m", "15m"]
    )
    
    interval_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m"
    }
    
    # yf_period and interval setup
    yf_period = "1d"
    yf_interval = interval_map.get(interval, "1d")  # Default to "1d" if not found

    # Fetch data based on selected period, interval, and stock symbol
    data = fetch_data(stock_symbol, yf_interval, yf_period)

    if data.empty:
        st.error("Failed to retrieve data. Please try again.")
        return

    # Calculate daily returns
    close_data = data['Close']
    data_returns = close_data.pct_change().dropna()

    # Define Lorentzian distance function
    def lorentzian_distance(x, y):
        return np.log(1 + (x - y)**2)

    # Compute Lorentzian distances between consecutive returns
    if len(data_returns) < 2:
        st.warning("Not enough data to compute Lorentzian distances.")
        lorentzian_distances = np.array([])
    else:
        lorentzian_distances = [lorentzian_distance(data_returns[i], data_returns[i + 1]) for i in range(len(data_returns) - 1)]
        lorentzian_distances = np.array(lorentzian_distances)

    # Define a threshold to identify anomalies
    if len(lorentzian_distances) > 0:
        threshold = lorentzian_distances.mean() + 2 * lorentzian_distances.std()
        anomalies = lorentzian_distances > threshold
        anomaly_indices = np.where(anomalies)[0]
        anomaly_dates = data_returns.index[anomaly_indices]
    else:
        threshold = None
        anomaly_dates = []

    # Prepare the data for candlestick chart
    data['Anomalies'] = np.where(data.index.isin(anomaly_dates), data['Close'], np.nan)

    # Calculate support and resistance levels
    latest_support, latest_resistance = calculate_support_resistance(data)

    if latest_support is None or latest_resistance is None:
        st.error("Failed to calculate support and resistance levels.")
        return

    # Create candlestick chart
    fig = go.Figure()

    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candlestick'
    ))

    # Add support and resistance lines
    fig.add_trace(go.Scatter(
        x=data.index,
        y=[latest_support] * len(data),
        mode='lines',
        name='Support',
        line=dict(color='green', width=2, dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=data.index,
        y=[latest_resistance] * len(data),
        mode='lines',
        name='Resistance',
        line=dict(color='blue', width=2, dash='dash')
    ))

    # Add anomalies as scatter points
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Anomalies'],
        mode='markers',
        name='Anomalies',
        marker=dict(color='yellow', size=10, symbol='x')
    ))

    # Format date range
    start_date = data.index.min().strftime('%Y-%m-%d')
    end_date = data.index.max().strftime('%Y-%m-%d')

    # Update layout
    fig.update_layout(
        title=f'{stock_symbol} Stock Price from {start_date} to {end_date} with Anomalies, Support, and Resistance ({interval})',
        xaxis_title='Date',
        yaxis_title='Stock Price',
        xaxis_rangeslider_visible=False,  # Hide range slider
        xaxis_tickformat='%H:%M',  # Format x-axis to show hours and minutes
    )

    # Display the chart
    st.plotly_chart(fig)

    # News section
    st.header(f"Recent {stock_symbol} News")

    # Fetch and display news
    news_items = fetch_stock_news(stock_symbol)

    if not news_items:
        st.write("No news found.")
        return

    for item in news_items:
        st.subheader(item['title'])
        st.write(f"Published: {item['publishedAt']}")
        st.write(f"[Read more]({item['url']})")
        st.write("---")

    # Predict the next interval's return
    st.header("Prediction")

    def predict_next_return(data_returns, lorentzian_distances):
        if len(data_returns) < 2:
            st.warning("Not enough data to predict the next interval's return.")
            return 0
        
        recent_distance = lorentzian_distance(data_returns[-2], data_returns[-1])
        if threshold and recent_distance > threshold:
            st.warning("Anomaly detected. Predicted return may be highly volatile.")
        else:
            st.info("No anomaly detected. Predicted return is based on historical average.")
        return data_returns.mean()

    predicted_return = predict_next_return(data_returns, lorentzian_distances)
    st.write(f"Predicted next interval's return: {predicted_return:.4f}")

if __name__ == "__main__":
    main()
