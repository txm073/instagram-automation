import os, sys
import warnings
from typing import List, Tuple, Dict, Any

from instagrapi import Client
from instagrapi.types import User, UserShort

warnings.warn(
    "Use of the Instagram v1 mobile API is not recommended as the API is deprecated",
    DeprecationWarning
)


def api_func(fn):
    def inner(*args, **kwargs):
        result = fn(*args, **kwargs)
        return result
    return inner


class InstagramAPI(Client):
    _inst = None
    _auth_user = None
    _auth_pwd = None

    def __new__(cls, *args, **kwargs):
        """Method override to ensure that only one instance of the Client class is created"""
        if cls._inst is None:
            cls._inst = super(InstagramAPI, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self, username, pwd, *args, **kwargs):
        super(InstagramAPI, self).__init__(*args, **kwargs)
        
    
    def get_following(self, username: str) -> List[UserShort]:
        """Get all the users that a specific user is following"""
        uid = super(InstagramAPI, self).user_id_from_username(username)
        users = super(InstagramAPI, self).user_following(uid).values()
        return users

    def get_followers(self, username: str):# -> List[UserShort]:
        """Get all the followers of a specific user"""
        uid = super(InstagramAPI, self).user_id_from_username(username)
        users = super(InstagramAPI, self).user_followers(uid).values()
        return users

    def login(self, username: str, pwd: str) -> Tuple[int, str]:
        """Authenticate using the Instagram v1 mobile API"""
        try:
            status = super(InstagramAPI, self).login(username, pwd)
        except Exception as e:
            return 1, str(e)
        return 0, "success"

    def as_json(self, obj):
        """Create a JSON response to be returned from the proxy server"""
        pass


client = InstagramAPI()

def execute(command: Dict[Any, Any]) -> str:
    func = command["function"]
    

if __name__ == "__main__" and "--local" in sys.argv:
    pass