from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
