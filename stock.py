import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

def app():
    st.title("Stock Chart")

    # User input for stock ticker
    ticker = st.text_input("Enter Stock Ticker", "AAPL")  # Default: Apple

    # Fetch stock data
    stock_data = yf.download(ticker, period="1y", interval="1d")  # 1 month data with 1-hour intervals

    # Create stock chart
    fig = go.Figure(data=[go.Candlestick(x=stock_data.index,
                                         open=stock_data['Open'],
                                         high=stock_data['High'],
                                         low=stock_data['Low'],
                                         close=stock_data['Close'])])

    fig.update_layout(title=f"{ticker} Stock Price Chart", xaxis_title="Date", yaxis_title="Price (USD)")

    st.plotly_chart(fig)
