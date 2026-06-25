
import sys
import os
from io import StringIO

sys.stdout = sys.stderr = open('app_log.txt', 'w')
from app import app

print("Starting Flask app...", file=sys.stdout)
sys.stdout.flush()
app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
