import streamlit as st
import stock
import crypto
import forex
import stock_news_page  # Import the stock news page function

# Set the page layout to wide to accommodate the content better
st.set_page_config(layout="wide")

# Sidebar for navigation
st.sidebar.title("Navigation")

# Radio button for selecting the chart type (placed in the sidebar)
page = st.sidebar.radio("Choose a chart", ["Stock Chart", "Crypto Chart", "Forex Exchange", "Stock News"])

# Navigation logic based on the selected option in the sidebar
if page == "Stock Chart":
    stock.app()
elif page == "Crypto Chart":
    crypto.app()
elif page == "Forex Exchange":
    forex.app()
elif page == "Stock News":
    stock_news_page.app()  # Call the stock news page function
