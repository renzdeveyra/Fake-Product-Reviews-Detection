import json
import os
from transformers import pipeline

INPUT_DIR = "scraped_reviews"
OUTPUT_DIR = "sentiment_reviews"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the BERT sentiment analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_sentiment(text):
    result = sentiment_pipeline(text[:512])[0]  # Truncate to 512 tokens for BERT
    label = result['label'].lower()
    return label  # returns "positive" or "negative"

for filename in os.listdir(INPUT_DIR):
    if not filename.endswith("_top_reviews.json"):
        continue

    with open(os.path.join(INPUT_DIR, filename), 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    for review in reviews:
        full_text = (review.get('review_header', '') + " " + review.get('review_text', '')).strip()
        review['sentiment'] = analyze_sentiment(full_text)

    output_path = os.path.join(OUTPUT_DIR, filename.replace('_top_reviews.json', '_with_sentiment.json'))
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=4, ensure_ascii=False)

    print(f"✅ Saved: {output_path}")
