import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

def app():
    st.title("Crypto Chart")

    # User input for crypto ticker
    ticker = st.text_input("Enter Crypto Ticker", "BTC-USD")  # Default: Bitcoin

    # Fetch crypto data
    crypto_data = yf.download(ticker, period="1mo", interval="1h")  # 1 month data with 1-hour intervals

    # Create crypto chart
    fig = go.Figure(data=[go.Candlestick(x=crypto_data.index,
                                         open=crypto_data['Open'],
                                         high=crypto_data['High'],
                                         low=crypto_data['Low'],
                                         close=crypto_data['Close'])])

    fig.update_layout(title=f"{ticker} Crypto Price Chart", xaxis_title="Date", yaxis_title="Price (USD)")

    st.plotly_chart(fig)
