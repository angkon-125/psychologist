"""
ZARA application launcher.

Sets up structured logging, then starts the Flask application server.
"""

from logger import setup_logging, get_logger

# Configure logging before importing app (so app module picks it up)
setup_logging()
logger = get_logger("run_app")

from app import app

if __name__ == "__main__":
    import os

    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))

    logger.info("Starting ZARA Flask app on %s:%d (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug, use_reloader=False)
else:
    # Allow WSGI servers (gunicorn, waitress) to import directly
    logger.info("ZARA app loaded for WSGI deployment")
