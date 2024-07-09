import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Define a dictionary mapping stock names to their ticker symbols
stocks = {
    "Google": "GOOGL",
    "Meta": "META",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA"
}

# Page title and description
st.title('Interactive Stock Chart App')
st.write('Select a stock to view its chart:')

# Dropdown menu to select stock
selected_stock = st.selectbox('Select Stock', list(stocks.keys()))

# Display the selected stock's name and symbol
st.write(f'Stock selected: {selected_stock} ({stocks[selected_stock]})')

# Calculate date ranges for the last 5 years
end_date = datetime.now()
start_date = end_date - timedelta(days=5*365)  # Assuming 365 days per year

# Fetch historical data from Yahoo Finance
ticker_symbol = stocks[selected_stock]
stock_data = yf.download(ticker_symbol, start=start_date, end=end_date)

# Display the data
st.write(stock_data)

# Plot the data with customized x-axis date format
import plotly.graph_objs as go

fig = go.Figure()
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name='Close'))

fig.update_layout(
    title=f'{selected_stock} Stock Price',
    xaxis_title='Date',
    yaxis_title='Price',
    xaxis_tickformat='%b %y'  # Format x-axis ticks as Day Month Year (e.g., 01 Jan 20)
)

st.plotly_chart(fig)
