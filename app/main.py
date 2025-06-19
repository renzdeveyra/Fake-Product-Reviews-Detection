from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import ReviewText, SentimentResponse
from app.services.sentiment import analyze_sentiment

# Create the FastAPI app instance
app = FastAPI(
    title="Amazon Review Analyzer",
    description="API for scraping and analyzing Amazon product reviews",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Amazon Review Analyzer API"}

@app.post("/analyze/sentiment", response_model=SentimentResponse)
async def sentiment_analysis(review: ReviewText):
    """Analyze the sentiment of a review text."""
    result = analyze_sentiment(review.text)
    return result
