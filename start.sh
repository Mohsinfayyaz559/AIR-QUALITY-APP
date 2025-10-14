#!/bin/bash

# Start FastAPI in background
echo "Starting FastAPI server..."
uvicorn api:app --host 0.0.0.0 --port 8000 &

# Wait a bit to make sure FastAPI starts
#sleep 3

# Start Streamlit (main interface for Hugging Face)
echo "Starting Streamlit app..."
streamlit run ui.py --server.port 7860 --server.address 0.0.0.0

