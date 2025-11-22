import yfinance as yf
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime
import time
import requests
import xml.etree.ElementTree as ET

# --- CONFIGURATION ---
# "reversion" = Buy when RSI is low (Dip Buying)
# "trend"     = Sell when Price < SMA50 (Momentum Trading)
STRATEGY_MODE = "trend" 

class StockAgent:
    def __init__(self, tickers):
        self.tickers = tickers
        self.analyzer = SentimentIntensityAnalyzer()
        self.results = []

    def calculate_rsi(self, ticker_symbol, period=14):
        """ Calculates RSI from historical data. """
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="3mo")
            
            if hist.empty: return 50

            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1]
        except Exception:
            return 50

    def get_sentiment(self, ticker_symbol):
        """ Fetches Google News RSS and scores sentiment. """
        url = f"https://news.google.com/rss/search?q={ticker_symbol}+stock&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            root = ET.fromstring(response.content)
            scores = []
            
            for item in root.findall('./channel/item')[:5]:
                title = item.find('title').text
                scores.append(self.analyzer.polarity_scores(title)['compound'])
            
            if not scores: return 0, "Neutral"

            avg_score = sum(scores) / len(scores)
            
            if avg_score > 0.05: mood = "Bullish"
            elif avg_score < -0.05: mood = "Bearish"
            else: mood = "Neutral"
                
            return avg_score, mood
        except Exception:
            return 0, "Neutral"

    def get_advanced_metrics(self, ticker_symbol):
        """ Fetches Price, Valuation, Analyst Targets, Volume, and 52W Range. """
        ticker = yf.Ticker(ticker_symbol)
        try:
            info = ticker.info
        except:
            info = {}

        price = info.get('currentPrice', 0)
        peg_ratio = info.get('pegRatio')
        pe_ratio = info.get('trailingPE')
        fwd_pe = info.get('forwardPE')
        
        target_price = info.get('targetMeanPrice', price)
        upside = ((target_price - price) / price) * 100 if price and target_price else 0
        
        sma_50 = info.get('fiftyDayAverage', price)
        rsi = self.calculate_rsi(ticker_symbol)
        
        avg_vol = info.get('averageVolume10days', 0)
        curr_vol = info.get('volume', 0)
        vol_strength = (curr_vol / avg_vol) if avg_vol else 1.0
        
        low_52 = info.get('fiftyTwoWeekLow', price)
        high_52 = info.get('fiftyTwoWeekHigh', price)
        
        if high_52 != low_52:
            range_pos = ((price - low_52) / (high_52 - low_52)) * 100
        else:
            range_pos = 50

        return {
            "price": price,
            "peg": peg_ratio,
            "pe": pe_ratio,
            "fwd_pe": fwd_pe,
            "upside": upside,
            "rsi": rsi,
            "sma_50": sma_50,
            "vol_strength": vol_strength,
            "range_pos": range_pos
        }

    def calculate_score(self, data, sent_score):
        score = 50 
        reasons = []

        # 1. Valuation
        if data['peg'] and data['peg'] < 1.0:
            score += 20
            reasons.append("Undervalued (PEG)")
        elif data['peg'] and data['peg'] > 2.0:
            score -= 20
            reasons.append("Overvalued (PEG)")
        elif data['fwd_pe'] and data['pe'] and data['fwd_pe'] < data['pe']:
            score += 10
            reasons.append("Improving Earnings")

        # 2. Analyst Consensus
        if data['upside'] > 20:
            score += 15
            reasons.append("High Analyst Upside")
        elif data['upside'] < 0:
            score -= 10
            reasons.append("Analyst Downside")

        # 3. Technicals (Strategy Dependent)
        if STRATEGY_MODE == "reversion":
            # Buy the Dip Logic
            if data['rsi'] < 30:
                score += 15
                reasons.append("Oversold RSI")
            elif data['rsi'] > 70:
                score -= 15
                reasons.append("Overbought RSI")
        
        elif STRATEGY_MODE == "trend":
            # Trend Following Logic (Punish Downtrends)
            if data['price'] < data['sma_50']:
                score -= 25 # Heavy penalty for being below SMA50
                reasons.append("Below 50SMA (Downtrend)")
            else:
                score += 10
                reasons.append("Uptrend (>50SMA)")
            
            if data['rsi'] < 40:
                score -= 10 # In trend mode, low RSI = weak momentum
                reasons.append("Weak Momentum")

        # 4. Sentiment
        if sent_score > 0.1:
            score += 10
            reasons.append("Positive News")
        elif sent_score < -0.1:
            score -= 10
            reasons.append("Negative News")

        score = max(0, min(100, score))
        
        if score >= 80: signal = "STRONG BUY"
        elif score >= 60: signal = "BUY"
        elif score <= 20: signal = "STRONG SELL"
        elif score <= 40: signal = "SELL"
        else: signal = "HOLD"

        return score, signal, ", ".join(reasons[:3])

    def run_analysis(self):
        print(f"--- Pro Stock Analysis Agent ({STRATEGY_MODE.upper()} MODE) ---")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        for t in self.tickers:
            print(f"Analyzing {t}...")
            
            sent_score, sent_mood = self.get_sentiment(t)
            data = self.get_advanced_metrics(t)
            score, signal, key_factors = self.calculate_score(data, sent_score)

            self.results.append({
                "Ticker": t,
                "Price": data['price'],
                "Signal": signal,
                "Score": score,
                "Key Factors": key_factors,
                "RSI": float(f"{data['rsi']:.2f}"),
                "Analyst Upside (%)": float(f"{data['upside']:.2f}"),
                "Vol Ratio": float(f"{data['vol_strength']:.2f}"),
                "Sentiment": sent_mood,
                "Trailing PE": data['pe'],
                "Forward PE": data['fwd_pe']
            })
            time.sleep(0.5)
                
        return pd.DataFrame(self.results)

if __name__ == "__main__":
    my_watchlist = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMD", "INTC", "AMZN", "META", "NFLX", "HIMS", "PLTR", "COIN", "UBER", "SHOP"]
    
    agent = StockAgent(my_watchlist)
    df = agent.run_analysis()
    
    if not df.empty:
        cols = ["Ticker", "Price", "Signal", "Score", "Key Factors", "RSI", "Analyst Upside (%)", "Vol Ratio", "Trailing PE", "Forward PE"]
        print("\n" + "="*90)
        print(df[cols].to_string(index=False))
        print("="*90)
        
        filename = f"Pro_Stock_Report_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"\nPro Report saved to {filename}")
    else:
        print("No data found.")