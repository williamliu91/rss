import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

def app():
    st.title("Forex Exchange Chart")

    # Input for selecting forex pair (e.g., EUR/USD)
    pair = st.text_input("Enter forex pair", "EURUSD=X")

    # Download forex data
    data = yf.download(pair, start="2022-01-01", end="2024-01-01")

    # Plot the forex chart
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'])])

    fig.update_layout(title=f"{pair} Exchange Rate", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig)
