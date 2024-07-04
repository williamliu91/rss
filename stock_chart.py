import streamlit as st
import yfinance as yf
import pandas as pd

# Title of the app
st.title("Stock Price App")

# Header
st.markdown("""
# Google Stock Price
Shown are the stock **closing price** and **volume** of Google.
""")

# Define the ticker symbol
tickerSymbol = 'GOOGL'

# Get data on this ticker
tickerData = yf.Ticker(tickerSymbol)

# Get the historical prices for this ticker
tickerDf = tickerData.history(period='1d', start='2010-5-31', end='2020-5-31')

# Line chart for closing price
st.header("Closing Price")
st.line_chart(tickerDf.Close)

# Line chart for volume
st.header("Volume")
st.line_chart(tickerDf.Volume)
