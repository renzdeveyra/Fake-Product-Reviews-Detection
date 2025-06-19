from transformers import pipeline

# Load the sentiment analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_sentiment(text: str):
    """Analyze the sentiment of the given text."""
    result = sentiment_pipeline(text[:512])[0]  # Truncate to 512 tokens for BERT
    return {
        "text": text,
        "sentiment": result['label'].lower(),
        "score": float(result['score'])
    }