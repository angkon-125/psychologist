## Dependency Management System

This repository uses **pip** with a single `requirements.txt` file as its sole dependency management mechanism. There are no advanced package managers (Poetry, Pipenv), no lockfiles, no vendoring strategy, and no private registry configuration.

### Approach

- **Package Manager**: Standard Python `pip`
- **Manifest File**: Single `psychologist/requirements.txt` at the project root level
- **Installation Command**: `pip install -r requirements.txt` (documented in README.md)
- **No Lockfile**: No `requirements.lock`, `Pipfile.lock`, or `poetry.lock` exists
- **No Virtual Environment Configuration**: No `.venv`, `pyproject.toml`, or environment isolation tooling committed to the repo

### Key Files

- **`psychologist/requirements.txt`** — The only dependency manifest, listing 18 third-party packages with minimum version constraints using `>=` syntax
- **`psychologist/README.md`** — Documents installation via `pip install -r requirements.txt` and optional production dependency (`gunicorn`) installed separately

### Dependencies Declared

The `requirements.txt` groups dependencies by functional area:

| Category | Packages |
|---|---|
| Web Framework | `flask>=2.3.0`, `flask-cors>=4.0.0` |
| Visualization/CV | `matplotlib>=3.7.0`, `networkx>=3.0`, `PyQt6>=6.4.0`, `opencv-python>=4.8.0` |
| Audio/Voice I/O | `sounddevice>=0.4.6`, `numpy>=1.26.0`, `scipy>=1.11.0`, `librosa>=0.10.0`, `vosk>=0.3.45`, `faster-whisper>=1.0.0`, `pyttsx3>=2.90`, `pyaudio>=0.2.14`, `webrtcvad>=2.0.10` |
| Utilities | `pyyaml>=6.0`, `wave>=0.0.2` |

All version constraints use **minimum-version pinning** (`>=X.Y.Z`), which allows pip to resolve to the latest compatible version at install time. This provides flexibility but sacrifices reproducibility across environments.

### Architecture and Conventions

1. **Flat dependency list** — All dependencies are declared in a single file with no distinction between production, development, or optional dependencies. Test dependencies (e.g., `pytest`) are not listed, implying they must be installed manually.

2. **No transitive dependency locking** — Without a lockfile, two developers or deployment environments may resolve different transitive dependency trees for the same `requirements.txt`, potentially causing subtle incompatibilities.

3. **Optional production dependency documented separately** — `gunicorn` is mentioned in the README for production deployment but is not included in `requirements.txt`. Developers must install it manually via `pip install gunicorn`.

4. **No dependency grouping or extras** — Unlike `pyproject.toml` with `[project.optional-dependencies]`, there is no mechanism to install subsets (e.g., "voice-only" or "web-only"). All 18 packages are installed together.

5. **Standard library imports are implicit** — Modules like `os`, `math`, `typing`, `re`, `json`, `time`, `datetime`, `logging`, `pathlib`, `collections`, `copy`, `io`, `struct`, `array`, `threading`, `queue`, `uuid`, `hashlib`, `secrets`, `string`, `textwrap`, `unicodedata`, `subprocess`, `signal`, `sys`, `traceback`, `warnings`, `contextlib`, `functools`, `itertools`, `operator`, `enum`, `dataclasses`, `abc`, `inspect`, `dis`, `ast`, `tokenize`, `keyword`, `token`, `linecache`, `pdb`, `profile`, `cProfile`, `timeit`, `gc`, `weakref`, `types`, `pprint`, `reprlib`, `difflib`, `html`, `xml`, `csv`, `configparser`, `argparse`, `getopt`, `shutil`, `glob`, `fnmatch`, `stat`, `tempfile`, `gzip`, `bz2`, `lzma`, `zipfile`, `tarfile`, `sqlite3`, `dbm`, `pickle`, `shelve`, `marshal`, `copyreg`, `platform`, `errno`, `ctypes`, `concurrent`, `multiprocessing`, `asyncio`, `select`, `selectors`, `mmap`, `socket`, `ssl`, `ftplib`, `poplib`, `imaplib`, `smtplib`, `mailbox`, `mimetypes`, `base64`, `binascii`, `quopri`, `email`, `http`, `urllib`, `xmlrpc`, `ipaddress`, `cgi`, `cgitb`, `wsgiref`, `simplehttpserver`, `httpserver`, `webbrowser`, `turtle`, `cmd`, `shlex`, `tkinter`, `idlelib`, `doctest`, `unittest`, `test`, `bdb`, `faulthandler`, `atexit`, `readline`, `rlcompleter`, `site`, `code`, `codeop`, `compileall`, `py_compile`, `zipimport`, `pkgutil`, `modulefinder`, `runpy`, `importlib`, `distutils`, `ensurepip`, `venv`, `zipapp` are used throughout the codebase without being declared (as expected for stdlib).

### Rules for Developers

1. **Install dependencies**: Run `cd psychologist && pip install -r requirements.txt` from the project root.
2. **Adding new dependencies**: Append the package with a minimum version constraint (e.g., `newpackage>=1.0.0`) to `requirements.txt`. Do not use exact pins (`==`) unless absolutely necessary for compatibility.
3. **Production deployment**: Install `gunicorn` separately if deploying with a WSGI server: `pip install gunicorn`.
4. **Testing dependencies**: `pytest` and related test tools are not in `requirements.txt`. Install them manually: `pip install pytest`.
5. **Reproducibility warning**: Because there is no lockfile, document the Python version and consider generating a frozen snapshot (`pip freeze > requirements-frozen.txt`) for reproducible deployments.
6. **Offline models**: Voice models for Vosk, Whisper, and Piper must be downloaded separately and placed in `models/stt/vosk/` and `models/tts/` — these are not managed by pip.

### Gaps and Risks

- **No lockfile** means non-deterministic builds across environments.
- **No dev/prod separation** means all dependencies (including heavy CV/audio packages) are installed even for minimal use cases.
- **No CI/CD dependency caching** configuration visible in the repository structure.
- **No automated dependency update** mechanism (e.g., Dependabot, Renovate) configured.