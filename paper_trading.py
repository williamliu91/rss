import streamlit as st
import yfinance as yf
import pandas as pd
import os
import datetime

def app():
    # Title and Header
    st.title("📊 Real-Time Stock Lookup & Paper Trading")

    # Portfolio CSV File
    PORTFOLIO_FILE = "portfolio.csv"

    # Initialize Session State
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = pd.DataFrame(columns=["Symbol", "Shares", "Purchase Price"])
    if 'balance' not in st.session_state:
        st.session_state.balance = 100000  # Default balance if no file exists

    # Load Portfolio and Balance from CSV
    def load_portfolio_and_balance():
        if os.path.exists(PORTFOLIO_FILE):
            data = pd.read_csv(PORTFOLIO_FILE)
            if "Balance" in data.columns:
                balance = data["Balance"].iloc[0]
                portfolio = data.drop(columns=["Balance"])
                return portfolio, balance
        return pd.DataFrame(columns=["Symbol", "Shares", "Purchase Price"]), 100000

    # Save Portfolio and Balance to CSV
    def save_portfolio_and_balance(portfolio, balance):
        portfolio["Balance"] = [balance] + [None] * (len(portfolio) - 1)
        portfolio.to_csv(PORTFOLIO_FILE, index=False)

    # Function to Fetch Stock Data
    def get_stock_data(symbol):
        """Get latest stock data including price and basic info."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='1d')
            if df.empty:
                return None
            current_price = df['Close'].iloc[-1]
            info = {
                'symbol': symbol,
                'current_price': current_price,
                'volume': df['Volume'].iloc[-1],
                'open': df['Open'].iloc[-1],
                'high': df['High'].iloc[-1],
                'low': df['Low'].iloc[-1]
            }
            try:
                info['name'] = ticker.info.get('longName', symbol)
            except:
                info['name'] = symbol
            return info
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    # Load portfolio and balance at start
    st.session_state.portfolio, st.session_state.balance = load_portfolio_and_balance()

    st.markdown("""
    Monitor real-time market prices and engage in paper trading.
    Start with a virtual balance of **$100,000**, and build your portfolio!
    """)

    # Stock Symbol Input
    symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, GOOGL)", "").upper()

    if symbol:
        with st.spinner(f'Fetching data for {symbol}...'):
            stock_data = get_stock_data(symbol)

            if stock_data:
                st.markdown(f"<h1 style='font-size: 24px;'>{stock_data['name']} ({stock_data['symbol']})</h1>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"<h3 style='font-size: 16px;'>💵 Current Price: ${stock_data['current_price']:.2f}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='font-size: 16px;'>🔄 Volume: {stock_data['volume']:,}</h3>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<h3 style='font-size: 16px;'>📈 Day High: ${stock_data['high']:.2f}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='font-size: 16px;'>📉 Day Low: ${stock_data['low']:.2f}</h3>", unsafe_allow_html=True)
                    
                st.markdown("---")

    # Paper Trading Section
    st.subheader("📋 Paper Trading")
    col1, col2 = st.columns([1, 1])  # Adjust column proportions as needed

    # Buy Section
    with col1:
        buy_quantity = st.number_input(
            "Enter quantity to buy", min_value=0, step=1, value=0, key="buy_quantity"
        )
        buy_button = st.button("Buy", key="buy_button")

    # Sell Section
    with col2:
        sell_quantity = st.number_input(
            "Enter quantity to sell", min_value=0, step=1, value=0, key="sell_quantity"
        )
        sell_button = st.button("Sell", key="sell_button")

    # Ensure stock data is fetched
    if symbol:
        with st.spinner(f'Fetching data for {symbol}...'):
            stock_data = get_stock_data(symbol)

        if stock_data:  # Only proceed if stock data is available
            # Buy Button Logic
            if buy_button:
                cost = buy_quantity * stock_data["current_price"]
                transaction_fee = cost * 0.002  # 0.2% transaction fee
                total_cost = cost + transaction_fee  # Total cost with fee
                transaction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current date and time

                if total_cost <= st.session_state.balance:
                    st.session_state.balance -= total_cost  # Deduct total cost with fee
                    existing = st.session_state.portfolio[
                        st.session_state.portfolio["Symbol"] == symbol
                    ]
                    if not existing.empty:
                        st.session_state.portfolio.loc[existing.index, "Shares"] += buy_quantity
                        st.session_state.portfolio.loc[existing.index, "Transaction Fee"] += transaction_fee  # Add fee
                        st.session_state.portfolio.loc[existing.index, "Transaction Date"] = transaction_date  # Add date
                    else:
                        st.session_state.portfolio = pd.concat(
                            [
                                st.session_state.portfolio,
                                pd.DataFrame(
                                    {
                                        "Symbol": [symbol],
                                        "Shares": [buy_quantity],
                                        "Purchase Price": [stock_data["current_price"]],
                                        "Transaction Fee": [transaction_fee],  # Add fee to new row
                                        "Transaction Date": [transaction_date],  # Add date to new row
                                    }
                                ),
                            ]
                        )
                    save_portfolio_and_balance(st.session_state.portfolio, st.session_state.balance)
                    st.success(f"Bought {buy_quantity} shares of {symbol} for ${cost:.2f} (Fee: ${transaction_fee:.2f}) on {transaction_date}")
                else:
                    st.error("Insufficient balance!")

            # Sell Button Logic
            if sell_button:
                existing = st.session_state.portfolio[
                    st.session_state.portfolio["Symbol"] == symbol
                ]
                if not existing.empty and existing["Shares"].iloc[0] >= sell_quantity:
                    st.session_state.portfolio.loc[existing.index, "Shares"] -= sell_quantity
                    proceeds = sell_quantity * stock_data["current_price"]
                    transaction_fee = proceeds * 0.002  # 0.2% transaction fee
                    net_proceeds = proceeds - transaction_fee  # Net proceeds after fee
                    transaction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current date and time
                    st.session_state.balance += net_proceeds
                    st.session_state.portfolio.loc[existing.index, "Transaction Fee"] += transaction_fee  # Add fee
                    st.session_state.portfolio.loc[existing.index, "Transaction Date"] = transaction_date  # Add date
                    st.session_state.portfolio = st.session_state.portfolio[
                        st.session_state.portfolio["Shares"] > 0
                    ]
                    save_portfolio_and_balance(st.session_state.portfolio, st.session_state.balance)
                    st.success(f"Sold {sell_quantity} shares of {symbol} for ${net_proceeds:.2f} (Fee: ${transaction_fee:.2f}) on {transaction_date}")
                else:
                    st.error("Not enough shares to sell!")

            st.markdown("---")

    # Portfolio Display Section
    st.subheader("📂 Portfolio")
    if not st.session_state.portfolio.empty:
        # Remove rows with NaN or invalid symbols from the portfolio
        valid_portfolio = st.session_state.portfolio.dropna(subset=["Symbol"])

        # Drop the "Balance" column before displaying the portfolio table
        valid_portfolio = valid_portfolio.drop(columns=["Balance"], errors="ignore")

        # Rename the columns as needed (make sure this happens first)
        valid_portfolio = valid_portfolio.rename(columns={
            "Transaction Date": "The Latest Transaction Date",  # Renaming "Transaction Date" column
            "Purchase Price": "The Latest Purchase Price",     # Renaming "Purchase Price" column
            "Transaction Fee": "Total Transaction Fee"         # Renaming "Transaction Fee" column
        })

        # Add a check to ensure stock data is available before calculating current value
        def get_current_value(symbol, shares):
            if pd.isna(symbol):  # Skip invalid symbols
                return 0
            stock_data = get_stock_data(symbol)
            if stock_data:
                return round(shares * stock_data['current_price'], 2)  # Round to 2 decimals
            else:
                return 0  # Return 0 if stock data is unavailable

        # Apply the current value calculation to the valid portfolio
        valid_portfolio['Current Value'] = valid_portfolio.apply(
            lambda row: get_current_value(row['Symbol'], row['Shares']), axis=1
        )

        # Round all relevant columns to 2 decimal points to ensure correct display
        valid_portfolio["The Latest Purchase Price"] = valid_portfolio["The Latest Purchase Price"].round(2)
        valid_portfolio["Total Transaction Fee"] = valid_portfolio["Total Transaction Fee"].round(2)
        valid_portfolio["Current Value"] = valid_portfolio["Current Value"].round(2)
        valid_portfolio["Shares"] = valid_portfolio["Shares"].round(2)

        # Ensure that figures are displayed with 2 decimal places using string formatting
        valid_portfolio["The Latest Purchase Price"] = valid_portfolio["The Latest Purchase Price"].apply(lambda x: f"{x:.2f}")
        valid_portfolio["Total Transaction Fee"] = valid_portfolio["Total Transaction Fee"].apply(lambda x: f"{x:.2f}")
        valid_portfolio["Current Value"] = valid_portfolio["Current Value"].apply(lambda x: f"{x:.2f}")
        valid_portfolio["Shares"] = valid_portfolio["Shares"].apply(lambda x: f"{x:.2f}")

        # Show the portfolio with the updated column names
        st.table(valid_portfolio)
    else:
        st.write("No shares in portfolio. Start trading to build your portfolio!")

    st.write(f"💰 **Updated Balance**: **${st.session_state.balance:,.2f}**")
