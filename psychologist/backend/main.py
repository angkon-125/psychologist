"""
ZARA Application Entry Point

Starts the Flask server, registers all agent API blueprints,
and initializes the Orchestrator with its specialist agents.
"""

import os
import sys
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Ensure root workspace is in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.config import config
from backend.api.shared import initialize_system
from backend.api.routes_chat import chat_bp
from backend.api.routes_voice import voice_bp
from backend.api.routes_memory import memory_bp
from backend.api.routes_tools import tools_bp
from backend.api.routes_evaluation import evaluation_bp

# Set up logging format
logging.basicConfig(
    level=config.get_log_level(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("zara.main")

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    
    # 1. Initialize the multi-agent system orchestrator
    logger.info("Initializing multi-agent architecture...")
    initialize_system()
    
    # 2. Register blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(evaluation_bp)
    
    # 3. Static frontend routes
    @app.route("/")
    def index():
        return send_from_directory(os.path.join(_project_root, "frontend"), "index.html")

    @app.route("/<path:path>")
    def static_file(path):
        return send_from_directory(os.path.join(_project_root, "frontend"), path)
    
    # 4. API routes
    @app.route("/api/health", methods=["GET"])
    def health():
        from backend.api.shared import orchestrator
        agents_health = {}
        for name, agent in orchestrator.specialists.items():
            agents_health[name] = agent.health_check()
            
        return jsonify({
            "status": "healthy",
            "orchestrator": orchestrator.health_check(),
            "specialists": agents_health
        })
        
    @app.route("/api/system/status", methods=["GET"])
    def status():
        from backend.api.shared import orchestrator
        status_info = {
            "orchestrator": orchestrator.get_info()
        }
        for name, agent in orchestrator.specialists.items():
            status_info[name] = agent.get_info()
            
        return jsonify(status_info)

    logger.info("App creation complete. Ready to serve.")
    return app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    
    logger.info("Starting ZARA multi-agent backend on %s:%d (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug)
