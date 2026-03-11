"""
PythonAnywhere WSGI Configuration
──────────────────────────────────
This file is used by PythonAnywhere to serve the Flask dashboard.

Setup:
1. Upload the SysProbe folder to /home/yourusername/SysProbe
2. In PythonAnywhere → Web tab → WSGI config file, replace contents with:

    import sys
    sys.path.insert(0, '/home/yourusername/SysProbe')
    from dashboard_server import app as application

3. Set the virtualenv path if using one
4. Reload the web app
"""

import sys
import os

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from dashboard_server import app as application
