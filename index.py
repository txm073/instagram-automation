"""
Import WSGI app object from source file as vercel looks for an "index.py" file
"""

from webapp import app, login
import sys

if "--runserver" in sys.argv:
    login("igapitest1", "0x369CF")
    app.run(debug=True, port=7041)