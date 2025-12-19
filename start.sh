#!/bin/bash
# Start the Backend Server in the background
uvicorn src.server:app --host 0.0.0.0 --port 8000 &

# Start the Scheduler in the background
python scheduler.py &

# Start the Frontend Dashboard
python -m streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0