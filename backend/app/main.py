from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import accounts
from app.api.routers import categories
from app.api.routers import postings

app = FastAPI()
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(postings.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
