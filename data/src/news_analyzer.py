# src/news_analyzer.py
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class NewsAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def get_sentiment(self, symbol):
        """Reads Google News and returns a sentiment score."""
        clean_symbol = symbol.replace(".NS", "")
        print(f"📰 Reading news for {clean_symbol}...")
        
        # Google News RSS Feed URL
        rss_url = f"https://news.google.com/rss/search?q={clean_symbol}+stock+India&hl=en-IN&gl=IN&ceid=IN:en"
        
        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"   ⚠️ Error fetching news: {e}")
            return 0, []
        
        total_score = 0
        count = 0
        headlines = []

        for entry in feed.entries[:5]:
            title = entry.title
            # VADER analyzes the text
            sentiment = self.analyzer.polarity_scores(title)
            score = sentiment['compound']
            
            total_score += score
            count += 1
            headlines.append(f"{title} (Score: {score})")
            
        if count == 0:
            return 0, ["No news found"]

        avg_score = total_score / count
        print(f"   📊 Sentiment Score: {avg_score:.2f}")
        return avg_score, headlines