import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objs as go  # Import Plotly's graph objects
from plotly.subplots import make_subplots  # Import make_subplots for subplots arrangement

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

# Calculate EMAs
stock_data['EMA20'] = stock_data['Close'].ewm(span=20, adjust=False).mean()
stock_data['EMA50'] = stock_data['Close'].ewm(span=50, adjust=False).mean()
stock_data['EMA200'] = stock_data['Close'].ewm(span=200, adjust=False).mean()

# Calculate RSI
delta = stock_data['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14, min_periods=1).mean()
avg_loss = loss.rolling(window=14, min_periods=1).mean()
rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

# Create a subplot figure with make_subplots
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                    subplot_titles=(f'{selected_stock} Stock Price with EMAs', 'RSI (14 days)', 'Volume'),
                    vertical_spacing=0.1)  # Adjust vertical spacing between subplots

# Add traces for stock price and EMAs to the main subplot
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name='Close'), row=1, col=1)
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['EMA20'], mode='lines', name='EMA 20'), row=1, col=1)
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['EMA50'], mode='lines', name='EMA 50'), row=1, col=1)
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['EMA200'], mode='lines', name='EMA 200'), row=1, col=1)

# Add RSI trace to the second subplot (RSI)
fig.add_trace(go.Scatter(x=stock_data.index, y=rsi, mode='lines', name='RSI (14 days)'), row=2, col=1)

# Add Volume trace to the third subplot (Volume)
fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='Volume'), row=3, col=1)

# Customize chart layout
fig.update_layout(
    title=f'{selected_stock} Stock Analysis',
    height=900,  # Adjust overall height of the chart
    showlegend=True,  # Show the legend to distinguish between different traces
)

# Update subplot axes titles and remove x-axis title for main chart
fig.update_yaxes(title_text='Price', row=1, col=1)
fig.update_yaxes(title_text='RSI', row=2, col=1)
fig.update_yaxes(title_text='Volume', row=3, col=1)
fig.update_xaxes(title_text='', row=1, col=1)  # Remove x-axis title for main chart

# Adjust subplot sizes
fig.update_yaxes(scaleanchor='x', scaleratio=0.6, row=1, col=1)  # Main chart (60% of height)
fig.update_yaxes(scaleanchor='x', scaleratio=0.2, row=2, col=1)  # RSI subplot (20% of height)
fig.update_yaxes(scaleanchor='x', scaleratio=0.2, row=3, col=1)  # Volume subplot (20% of height)

# Display the plotly chart
st.plotly_chart(fig)

# Export data as CSV
if st.button('Export Data as CSV'):
    csv_file = stock_data.to_csv(index=False)
    st.download_button(label='Download CSV', data=csv_file, file_name=f'{selected_stock}_data.csv', mime='text/csv')
