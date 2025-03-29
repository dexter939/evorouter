from app import app
import logging

if __name__ == "__main__":
    logging.info("Starting EvoRouter R4 Management Interface")
    app.run(host="0.0.0.0", port=5000, debug=True)
