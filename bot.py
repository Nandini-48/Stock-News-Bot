
import os
import yfinance as yf
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")  # Eventlet async mode

ALPHA_VANTAGE_API_KEY = "YT6ZNN6907UWED2Z"

# Function to get stock price
def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return round(data["Close"].iloc[-1], 2)
    return None

# Function to get stock news

def get_stock_news(ticker):
    try:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey=YT6ZNN6907UWED2Z"
        
        print("🔍 Fetching news from Alpha Vantage API...")  # Debugging
        print(f"🔗 API URL: {url}")  
        
        response = requests.get(url)
        print(f"📡 API Response Status: {response.status_code}")  
        
        try:
            json_response = response.json()
            print(f"📜 API Response JSON: {json_response}")  
        except Exception as e:
            print(f"🚨 JSON Parsing Error: {e}")  
            return ["Error parsing news data."]

        if response.status_code == 200 and "feed" in json_response:
            articles = []
            for article in json_response["feed"][:2]:  # Get top 2 news
                title = article.get("title", "No Title")
                link = article.get("url", "#")
                sentiment = article.get("overall_sentiment_label", "Neutral")
                news_entry = f"📰 {title} ({sentiment}) 🔗 {link}"
                articles.append(news_entry)

            print(f"📰 News Fetched: {articles}")  
            return articles

        print("⚠️ No news available from API.")
        return ["No recent news available."]
    
    except Exception as e:
        print(f"🚨 Error fetching news: {e}")
        return ["Error fetching news."]

# Function to get market sentiment (Bullish / Bearish)
def get_market_sentiment(ticker):
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        news = response.json()
        positive, negative = 0, 0
        for article in news.get("feed", []):
            if "bullish" in article.get("title", "").lower():
                positive += 1
            elif "bearish" in article.get("title", "").lower():
                negative += 1
        return "Bullish" if positive > negative else "Bearish"
    return "Neutral"

# Add a test route to check if server is running
@app.route('/')
def index():
    return "Server is running!"

# Socket event for stock updates
@socketio.on("subscribe_stock")
def send_stock_data(data):
    ticker = data.get("ticker", "TSLA").upper()
    print(f"✅ Received stock subscription request: {ticker}")  # Debugging Step

    price = get_stock_price(ticker)
    print(f"💰 Stock Price Fetched: {price}")  # Debugging Step

    news = get_stock_news(ticker)  # 🛑 API Call
    print(f"📰 News Received in Function: {news}")  # Debugging Step

    sentiment = get_market_sentiment(ticker)
    print(f"📊 Market Sentiment Fetched: {sentiment}")  # Debugging Step

    if price:
        socketio.emit("stock_update", {"ticker": ticker, "price": price, "news": news, "sentiment": sentiment})
    else:
        socketio.emit("stock_update", {"error": "Invalid stock ticker or data not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render dynamically assigns a port
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)


