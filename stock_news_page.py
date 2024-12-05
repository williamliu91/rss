import streamlit as st
import feedparser

def app():
    st.title("Stock News RSS Feed")

    # Input for selecting stock ticker (e.g., GOOGL, AAPL)
    ticker = st.text_input("Enter a ticker symbol (e.g., GOOGL, AAPL, MSFT):", value="GOOGL").upper()

    if ticker:
        # Fetch the stock news using RSS feed
        feed_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        feed = feedparser.parse(feed_url)

        if feed.entries:
            st.subheader(f"Recent News for {ticker}:")
            for entry in feed.entries:
                st.write(f"**Title:** {entry.title}")
                st.write(f"**Link:** [Read more]({entry.link})")
                st.write(f"**Published:** {entry.published}")
                st.write("---")
        else:
            st.write("No news found for the given ticker symbol.")
