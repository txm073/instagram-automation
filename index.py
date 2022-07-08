"""
Import WSGI app object from source file as vercel looks for an "index.py" file
"""

from webapp import app
import sys

if "--runserver" in sys.argv:
    app.run(debug=True, port=7041)