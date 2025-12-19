import uvicorn

if __name__ == "__main__":
    print("🚀 Starting AI Trading Server...")
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)