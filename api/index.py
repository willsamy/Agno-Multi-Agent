# Vercel entry point
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main FastAPI app
from main import app

# Export the app for Vercel
handler = app