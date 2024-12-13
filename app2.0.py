import streamlit as st
import yfinance as yf
import pandas as pd
import os
import datetime


import streamlit as st
import stock
import crypto
import forex
import stock_news_page
import paper_trading  # Import the paper trading module


# Sidebar for navigation
st.sidebar.title("Navigation")

# Radio button for selecting the chart type (placed in the sidebar)
page = st.sidebar.radio("Choose a chart", ["Stock Chart", "Crypto Chart", "Forex Exchange", "Stock News", "Paper Trading"])

# Navigation logic based on the selected option in the sidebar
if page == "Stock Chart":
    stock.app()
elif page == "Crypto Chart":
    crypto.app()
elif page == "Forex Exchange":
    forex.app()
elif page == "Stock News":
    stock_news_page.app()
elif page == "Paper Trading":
    paper_trading.app()  # Call the paper trading page function