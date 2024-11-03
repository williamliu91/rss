import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
from fredapi import Fred
import base64

# Function to load the image and convert it to base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Path to the locally stored QR code image
qr_code_path = "qrcode.png"  # Ensure the image is in your app directory

# Convert image to base64
qr_code_base64 = get_base64_of_bin_file(qr_code_path)

# Custom CSS to position the QR code close to the top-right corner under the "Deploy" area
st.markdown(
    f"""
    <style>
    .qr-code {{
        position: fixed;  /* Keeps the QR code fixed in the viewport */
        top: 10px;       /* Sets the distance from the top of the viewport */
        right: 10px;     /* Sets the distance from the right of the viewport */
        width: 200px;    /* Adjusts the width of the QR code */
        z-index: 100;    /* Ensures the QR code stays above other elements */
    }}
    </style>
    <img src="data:image/png;base64,{qr_code_base64}" class="qr-code">
    """,
    unsafe_allow_html=True
)


# Add FRED API configuration
try:
    with open('fred.txt') as f:
        FRED_API_KEY = f.read().strip()
    fred = Fred(api_key=FRED_API_KEY)
except FileNotFoundError:
    st.warning("fred.txt file not found. Risk-free rate functionality will be disabled.")
    fred = None
except Exception as e:
    st.warning(f"Error initializing FRED API: {str(e)}")
    fred = None

@st.cache_data
def get_risk_free_rate():
    """Fetch the current risk-free rate (10-year Treasury yield) from FRED"""
    if not fred:
        return None
    try:
        ten_year_yield = fred.get_series('DGS10')
        return ten_year_yield.tail(1).values[0] / 100  # Convert percentage to decimal
    except Exception as e:
        st.warning(f"Unable to fetch risk-free rate: {str(e)}")
        return None

@st.cache_data
def get_market_return():
    """Calculate average annual market return for S&P 500 over the last 10 years"""
    sp500 = yf.Ticker("^GSPC")
    history = sp500.history(period="10y")
    
    # Resample the data to get annual 'Close' values at year-end
    annual_data = history['Close'].resample('Y').last()
    
    # Calculate annual returns
    annual_returns = annual_data.pct_change().dropna() * 100  # Convert to percentage
    
    # Calculate the average annual market return
    market_return = annual_returns.mean() / 100  # Convert to decimal
    return market_return

@st.cache_data
def load_data(ticker):
    data = yf.download(ticker)
    return data

def calculate_sharpe_ratio(data, risk_free_rate, window=252):
    """Calculate rolling Sharpe ratio"""
    if risk_free_rate is None:
        return None
        
    # Calculate daily returns
    daily_returns = data['Close'].pct_change()
    
    # Calculate excess returns over risk-free rate
    excess_returns = daily_returns - (risk_free_rate / 252)  # Daily risk-free rate
    
    # Calculate rolling metrics
    rolling_return = excess_returns.rolling(window=window).mean() * 252  # Annualized return
    rolling_std = daily_returns.rolling(window=window).std() * (252 ** 0.5)  # Annualized volatility
    
    # Calculate Sharpe ratio
    sharpe_ratio = rolling_return / rolling_std
    return sharpe_ratio

def add_ema(data, periods):
    for period in periods:
        data[f'EMA_{period}'] = data['Close'].ewm(span=period, adjust=False).mean()
    return data

def add_rsi(data, window=14):
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

def add_macd(data):
    short_ema = data['Close'].ewm(span=12, adjust=False).mean()
    long_ema = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = short_ema - long_ema
    data['Signal Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    return data

@st.cache_data
def get_fundamental_metrics(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    # Get risk-free rate
    risk_free_rate = get_risk_free_rate()
    
    # Get market return
    market_return = get_market_return()

    # Fetch balance sheet and financials data
    balance_sheet = stock.balance_sheet
    financials = stock.financials

    # Get interest expense (from income statement) and total debt (from balance sheet)
    interest_expense = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index else 0
    long_term_debt = balance_sheet.loc['Long Term Debt'].iloc[0] if 'Long Term Debt' in balance_sheet.index else 0
    short_term_debt = balance_sheet.loc['Short Term Debt'].iloc[0] if 'Short Term Debt' in balance_sheet.index else 0
    total_debt = long_term_debt + short_term_debt

    # Get income statement to calculate tax rate using Tax Provision and Pretax Income
    tax_provision = financials.loc['Tax Provision'].iloc[0] if 'Tax Provision' in financials.index else 0
    pretax_income = financials.loc['Pretax Income'].iloc[0] if 'Pretax Income' in financials.index else 1  # Avoid division by zero

    # Calculate the effective tax rate
    tax_rate = tax_provision / pretax_income if pretax_income != 0 else 0

    # Calculate cost of debt (adjusted for taxes)
    cost_of_debt = (interest_expense / total_debt) * (1 - tax_rate) if total_debt != 0 else 0

    # Get market capitalization (market value of equity)
    market_cap = info.get('marketCap', None)

    # Calculate cost of equity using CAPM
    beta = info.get('beta', None)  # Beta from Yahoo Finance
    if beta is None:
        raise ValueError("Beta value not found. Please check the ticker information.")
    
    cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)

    # Calculate WACC
    V = market_cap + total_debt  # Total value (equity + debt)
    WACC = (market_cap / V) * cost_of_equity + (total_debt / V) * cost_of_debt * (1 - tax_rate)

    metrics = {
        'Risk-Free Rate': f"{risk_free_rate:.2%}" if risk_free_rate is not None else 'N/A',
        'Market Return': f"{market_return:.2%}" if market_return is not None else 'N/A',
        'P/E Ratio': info.get('trailingPE', 'N/A'),
        'ROE': info.get('returnOnEquity', 'N/A'),
        'ROA': info.get('returnOnAssets', 'N/A'),
        'Gross Margin': info.get('grossMargins', 'N/A'),
        'Profit Margin': info.get('profitMargins', 'N/A'),
        'Debt to Equity': info.get('debtToEquity', 'N/A'),
        'Current Ratio': info.get('currentRatio', 'N/A'),
        'Price to Book': info.get('priceToBook', 'N/A'),
        'Earnings Per Share': info.get('trailingEps', 'N/A'),
        'Dividend Yield': info.get('dividendYield', 'N/A'),
        'Tax Rate': f"{tax_rate:.2%}",  # New metric for tax rate
        'Cost of Debt': f"{cost_of_debt:.2%}",  # New metric for cost of debt
        'WACC': f"{WACC:.2%}",  # New metric for WACC
    }
    
    # Clean up metrics for display
    for key, value in metrics.items():
        if key in ['Risk-Free Rate', 'Market Return', 'Tax Rate', 'Cost of Debt', 'WACC']:
            continue  # Skip processing for these as they're already formatted
        if isinstance(value, (int, float)):
            metrics[key] = round(value, 2)
        elif value == 'N/A':
            metrics[key] = 'N/A'
        else:
            try:
                metrics[key] = round(float(value), 2)
            except ValueError:
                metrics[key] = 'N/A'
    
    return metrics

    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Get risk-free rate
    risk_free_rate = get_risk_free_rate()
    
    # Get market return
    market_return = get_market_return()

    # Fetch balance sheet and financials data
    balance_sheet = stock.balance_sheet
    financials = stock.financials

    # Get interest expense (from income statement) and total debt (from balance sheet)
    interest_expense = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index else 0
    total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0

    # Get income statement to calculate tax rate using Tax Provision and Pretax Income
    tax_provision = financials.loc['Tax Provision'].iloc[0] if 'Tax Provision' in financials.index else 0
    pretax_income = financials.loc['Pretax Income'].iloc[0] if 'Pretax Income' in financials.index else 1  # Avoid division by zero

    # Calculate the effective tax rate
    tax_rate = tax_provision / pretax_income if pretax_income != 0 else 0

    # Calculate cost of debt (adjusted for taxes)
    cost_of_debt = (interest_expense / total_debt) * (1 - tax_rate) if total_debt != 0 else 0

    metrics = {
        'Risk-Free Rate': f"{risk_free_rate:.2%}" if risk_free_rate is not None else 'N/A',
        'Market Return': f"{market_return:.2%}" if market_return is not None else 'N/A',
        'P/E Ratio': info.get('trailingPE', 'N/A'),
        'ROE': info.get('returnOnEquity', 'N/A'),
        'ROA': info.get('returnOnAssets', 'N/A'),
        'Gross Margin': info.get('grossMargins', 'N/A'),
        'Profit Margin': info.get('profitMargins', 'N/A'),
        'Debt to Equity': info.get('debtToEquity', 'N/A'),
        'Current Ratio': info.get('currentRatio', 'N/A'),
        'Price to Book': info.get('priceToBook', 'N/A'),
        'Earnings Per Share': info.get('trailingEps', 'N/A'),
        'Dividend Yield': info.get('dividendYield', 'N/A'),
        'Tax Rate': f"{tax_rate:.2%}",  # New metric for tax rate
        'Cost of Debt': f"{cost_of_debt:.2%}",  # New metric for cost of debt
    }
    
    # Clean up metrics for display
    for key, value in metrics.items():
        if key in ['Risk-Free Rate', 'Market Return', 'Tax Rate', 'Cost of Debt']:
            continue  # Skip processing for these as they're already formatted
        if isinstance(value, (int, float)):
            metrics[key] = round(value, 2)
        elif value == 'N/A':
            metrics[key] = 'N/A'
        else:
            try:
                metrics[key] = round(float(value), 2)
            except ValueError:
                metrics[key] = 'N/A'
    
    return metrics

    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Get risk-free rate
    risk_free_rate = get_risk_free_rate()
    
    # Get market return
    market_return = get_market_return()
    
    metrics = {
        'Risk-Free Rate': f"{risk_free_rate:.2%}" if risk_free_rate is not None else 'N/A',
        'Market Return': f"{market_return:.2%}" if market_return is not None else 'N/A',
        'P/E Ratio': info.get('trailingPE', 'N/A'),
        'ROE': info.get('returnOnEquity', 'N/A'),
        'ROA': info.get('returnOnAssets', 'N/A'),
        'Gross Margin': info.get('grossMargins', 'N/A'),
        'Profit Margin': info.get('profitMargins', 'N/A'),
        'Debt to Equity': info.get('debtToEquity', 'N/A'),
        'Current Ratio': info.get('currentRatio', 'N/A'),
        'Price to Book': info.get('priceToBook', 'N/A'),
        'Earnings Per Share': info.get('trailingEps', 'N/A'),
        'Dividend Yield': info.get('dividendYield', 'N/A'),
    }
    
    for key, value in metrics.items():
        if key in ['Risk-Free Rate', 'Market Return']:
            continue  # Skip processing for these as they're already formatted
        if isinstance(value, (int, float)):
            metrics[key] = round(value, 2)
        elif value == 'N/A':
            metrics[key] = 'N/A'
        else:
            try:
                metrics[key] = round(float(value), 2)
            except ValueError:
                metrics[key] = 'N/A'
    
    return metrics

@st.cache_data
def fetch_rss_feed(ticker):
    feed_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
    feed = feedparser.parse(feed_url)
    return feed

# Main app
st.title('Interactive Stock Chart with Technical Indicators and Fundamental Metrics')

# Sidebar for user inputs and news feed
st.sidebar.title('Stock Ticker and News')
ticker = st.sidebar.text_input('Enter Stock Ticker', 'GOOGL').upper()

# Load stock data
data = load_data(ticker)

# Get risk-free rate for Sharpe ratio calculation
risk_free_rate = get_risk_free_rate()

# Time period selection
periods = st.slider('Select Time Period (in days)', 30, 365, 180)

# EMA selection
selected_emas = st.multiselect('Select EMA periods', [200, 50, 20], default=[200, 50, 20])

# Indicator plots selection
add_rsi_plot = st.checkbox('Add RSI Subplot')
add_macd_plot = st.checkbox('Add MACD Subplot')

# Calculate Sharpe ratio if risk-free rate is available
if risk_free_rate is not None:
    data['Sharpe Ratio'] = calculate_sharpe_ratio(data, risk_free_rate)
    add_sharpe = st.checkbox('Add Sharpe Ratio Subplot')

st.subheader('Select Fundamental Metrics to Display')
metrics = get_fundamental_metrics(ticker)
default_metrics = ['Risk-Free Rate', 'Market Return', 'P/E Ratio', 'ROE', 'Profit Margin']
selected_metrics = st.multiselect('Choose metrics', list(metrics.keys()), default=default_metrics)

if selected_metrics:
    st.subheader('Fundamental Metrics')
    for i in range(0, len(selected_metrics), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(selected_metrics):
                metric = selected_metrics[i + j]
                cols[j].metric(label=metric, value=metrics[metric])

# Add selected EMAs to data
data = add_ema(data, selected_emas)

# Slice data for the selected period
data_period = data[-periods:]

# Add indicators if selected
if add_rsi_plot:
    data_period = add_rsi(data_period)

if add_macd_plot:
    data_period = add_macd(data_period)

# Calculate number of rows for subplots
rows = 1 + add_rsi_plot + add_macd_plot + (add_sharpe if risk_free_rate is not None else 0)

# Define ranges for plots
price_range = [data_period['Close'].min() * 0.95, data_period['Close'].max() * 1.05]
rsi_range = [0, 100]
macd_range = [0, 0]

if add_macd_plot:
    macd_range = [
        min(data_period['MACD'].min(), data_period['Signal Line'].min()) * 1.05,
        max(data_period['MACD'].max(), data_period['Signal Line'].max()) * 1.05
    ]

# Create subplots
subplot_titles = ['Price']
if add_rsi_plot:
    subplot_titles.append('RSI')
if add_macd_plot:
    subplot_titles.append('MACD')
if risk_free_rate is not None and add_sharpe:
    subplot_titles.append('Sharpe Ratio')

fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                    vertical_spacing=0.15,
                    row_heights=[0.5] + [0.25] * (rows - 1),
                    subplot_titles=subplot_titles)

# Add price candlestick trace
fig.add_trace(go.Candlestick(x=data_period.index,
                             open=data_period['Open'],
                             high=data_period['High'],
                             low=data_period['Low'],
                             close=data_period['Close'],
                             name='Candlesticks'), row=1, col=1)

# Add selected EMA traces
for period in selected_emas:
    fig.add_trace(go.Scatter(x=data_period.index, y=data_period[f'EMA_{period}'], 
                              mode='lines', name=f'EMA {period}'), row=1, col=1)

fig.update_yaxes(title_text='Price', row=1, col=1, range=price_range)

# Add RSI trace
if add_rsi_plot:
    fig.add_trace(go.Scatter(x=data_period.index, y=data_period['RSI'],
                             mode='lines', name='RSI'), row=2, col=1)
    fig.add_hline(y=70, line=dict(color='red', dash='dash'), row=2, col=1)
    fig.add_hline(y=30, line=dict(color='green', dash='dash'), row=2, col=1)
    fig.update_yaxes(title_text='RSI', range=rsi_range, row=2, col=1)

# Add MACD traces
if add_macd_plot:
    fig.add_trace(go.Scatter(x=data_period.index, y=data_period['MACD'], mode='lines', name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data_period.index, y=data_period['Signal Line'], mode='lines', name='Signal Line'), row=3, col=1)
    fig.update_yaxes(title_text='MACD', row=3, col=1, range=macd_range)

# Add Sharpe ratio trace
if risk_free_rate is not None and add_sharpe:
    fig.add_trace(go.Scatter(x=data_period.index, y=data_period['Sharpe Ratio'], mode='lines', name='Sharpe Ratio'), row=rows, col=1)
    fig.update_yaxes(title_text='Sharpe Ratio', row=rows, col=1)

# Final layout adjustments
fig.update_layout(height=800, title=f"{ticker} Stock Price with Indicators", xaxis_rangeslider_visible=False)
st.plotly_chart(fig)

# Sidebar for news feed
st.sidebar.title(f"{ticker} News Feed")
feed = fetch_rss_feed(ticker)
for entry in feed.entries[:10]:
    st.sidebar.write(f"[{entry.title}]({entry.link})")
