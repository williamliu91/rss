import streamlit as st
import feedparser

# Function to fetch and parse RSS feed
def fetch_rss_feed(ticker):
    # URL format for Yahoo Finance RSS feed
    feed_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
    feed = feedparser.parse(feed_url)
    return feed

# Streamlit app
def main():
    st.title("Stock News RSS Feed")

    # User input for ticker symbol
    ticker = st.text_input("Enter a ticker symbol (e.g., GOOGL, AAPL, MSFT):", value="GOOGL").upper()

    if ticker:
        with st.spinner("Fetching news..."):
            feed = fetch_rss_feed(ticker)
            
            if feed.entries:
                st.subheader(f"Recent News for {ticker}:")
                for entry in feed.entries:
                    st.write(f"**Title:** {entry.title}")
                    st.write(f"**Link:** [Read more]({entry.link})")
                    st.write(f"**Published:** {entry.published}")
                    st.write("---")
            else:
                st.write("No news found for the given ticker symbol.")

if __name__ == "__main__":
    main()
