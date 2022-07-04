import os, sys
import warnings
from typing import List, Tuple, Dict, Any, Callable

from instagrapi import Client
from instagrapi.types import User, UserShort

warnings.warn(
    "Use of the Instagram v1 mobile API is not recommended as the API is deprecated",
    DeprecationWarning
)

funcmap: Dict[str, Tuple[Callable, bool]] = {}

def api_func(funcname, json_response=True):
    def wrapper(fn):
        funcmap[funcname] = (fn, json_response)
        def inner(*args, **kwargs):
            result = fn(*args, **kwargs)
            return result
        return inner
    return wrapper


class InstagramAPI(Client):
    _inst = None
    _auth_user = None
    _auth_pwd = None

    def __new__(cls, *args, **kwargs):
        """Method override to ensure that only one instance of the Client class is created"""
        if cls._inst is None:
            cls._inst = super(InstagramAPI, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    @api_func("following", json_response=False)
    def get_following(self, username: str) -> List[UserShort]:
        """Get all the users that a specific user is following"""
        uid = super(InstagramAPI, self).user_id_from_username(username)
        users = super(InstagramAPI, self).user_following(uid).values()
        return users

    @api_func("followers")
    def get_followers(self, username: str) -> List[UserShort]:
        """Get all the followers of a specific user"""
        uid = super(InstagramAPI, self).user_id_from_username(username)
        users = super(InstagramAPI, self).user_followers(uid).values()
        return users

    @api_func("login", json_response=False)
    def login(self, username: str, pwd: str) -> Tuple[int, str]:
        """Authenticate using the Instagram v1 mobile API"""
        try:
            status = super(InstagramAPI, self).login(username, pwd)
        except Exception as e:
            return 1, str(e)
        return 0, "success"

    def as_json(self, obj: Any) -> Dict[str, Any]:
        """Create a JSON response to be returned from the proxy server"""
        return {}


client = InstagramAPI()

def execute(command: Dict[Any, Any]) -> str:
    try:
        func, do_json = funcmap.get(command["function"], (None, False))
        assert func is not None
        kwargs = command["kwargs"]
        kwargs["self"] = client
        result = func(**kwargs)
        if do_json:
            result = client.as_json(result)
            result["status"] = "success"
            return result
        return {"status": "success", "response": str(result)}

    except KeyError:
        return {"status": "error", "reason": "command missing key 'kwargs'"}
    
    except AssertionError:
        return {"status": "error", "reason": f"function {command['function']!r} not found"}
    
    except Exception:
        return {"status": "error", "reason": "unknown"}


if __name__ == "__main__" and "--local" in sys.argv:
    resp = execute({"function": "login", "kwargs": {"username": "igapitest1", "pwd": "0x369CF"}})
    print(resp)

    following = client.user_following(client.user_id_from_username("tom.barnes1_"))
    print(following)
    #resp = execute({"function": "following", "kwargs": {"username": "tom.barnes1_"}})
    #print(resp)
    