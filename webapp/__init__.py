from flask import Flask
from .api import InstagramAPI

client = InstagramAPI()
client.login("igapitest1", "0x2468AE")
app = Flask(__name__)

from . import routes