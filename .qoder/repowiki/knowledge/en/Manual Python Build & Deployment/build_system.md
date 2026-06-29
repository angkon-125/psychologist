The ZARA project employs a lightweight, manual build and deployment strategy centered around standard Python tooling, without automated build scripts, containerization, or CI/CD pipelines.

### Build & Compilation Approach
- **No Build System**: The project does not use `Makefile`, `setup.py`, `pyproject.toml`, or any custom build scripts. It relies on direct execution of Python source files.
- **Dependency Management**: Dependencies are managed via a flat `requirements.txt` file located in the `psychologist/` directory. Installation is performed manually using `pip install -r requirements.txt`.
- **Entry Point**: The application is launched via `python run_app.py`, which configures structured logging and starts the Flask development server. 

### Testing Strategy
- **Framework**: Uses `pytest` for testing.
- **Execution**: Tests are run manually via the command line: `python -m pytest tests/ -v`.
- **Coverage**: The test suite includes integration tests for API endpoints, safety edge cases, session persistence, and the interaction pipeline. Voice subsystem tests are separated due to hardware dependencies.

### Deployment & Packaging
- **Development Server**: The default launch uses Flask's built-in server (`app.run()`), configured via environment variables (`FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG`).
- **Production Recommendation**: The documentation suggests using `gunicorn` as a WSGI server for production deployments (e.g., `gunicorn -w 4 -b 0.0.0.0:5000 run_app:app`), but no configuration files (such as systemd units or supervisor configs) are provided.
- **No Containerization**: There are no `Dockerfile` or `docker-compose.yml` files present in the repository. Deployment assumes a host environment with Python 3.10+ and the required system-level libraries for audio processing (e.g., PortAudio).

### Developer Conventions
- **Manual Setup**: Developers must manually create a virtual environment and install dependencies.
- **Configuration**: All tunable parameters are centralized in `system_constants.py`, avoiding hardcoded values in logic.
- **Offline-First**: The build and runtime environment must support offline operation, requiring local models for STT (Vosk/Whisper) and TTS (Piper/eSpeak) to be pre-downloaded and placed in the `models/` directory.