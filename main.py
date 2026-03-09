import uvicorn


if __name__ == "__main__":
    try:
        # handler = app
        handler = None

        uvicorn.run(handler, host="0.0.0.0", port=8001)

    except Exception as e:
        print(f"Error in API handler: {e}")
