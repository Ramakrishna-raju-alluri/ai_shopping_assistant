import sys
import os
from pathlib import Path

# Ensure the current directory is in the Python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from main import app
    # For EB with Procfile, expose the FastAPI app directly
    application = app
except ImportError as e:
    print(f"Error importing main app: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise
