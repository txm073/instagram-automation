import json
import os, sys
import logging
import warnings
from typing import (
    List, 
    Tuple, 
    Dict, 
    Any, 
    Callable
)
from instagrapi import Client
from instagrapi.types import User, UserShort
from dotenv import load_dotenv
import requests

load_dotenv()
logging.getLogger("instagrapi").disabled = True
logging.getLogger("public_request").disabled = True
warnings.warn(
    "Use of the Instagram v1 mobile API is not recommended as the API is deprecated",
    DeprecationWarning
)

funcmap: Dict[str, Tuple[Callable, bool]] = {}


def _is_builtin_type(obj: Any) -> bool:
    return obj is None or isinstance(obj, ( 
        int, float, bool, complex, bytearray, memoryview, str, 
        bytes, slice, range, list, dict, set, type, super, staticmethod, classmethod
    ))

def api_func(funcname: str, json_response: bool = True) -> Callable:
    def wrapper(fn) -> Callable:
        funcmap[funcname] = (fn, json_response)
        def inner(*args, **kwargs) -> Any:
            result = fn(*args, **kwargs)
            return result
        return inner
    return wrapper


class InstagramAPI(Client):
    _inst: type = None
    _uid_cache: Dict[str, str] = {}

    def __new__(cls, *args, **kwargs):
        """Method override to ensure that only one instance of the class is created"""
        if cls._inst is None:
            cls._inst = super(InstagramAPI, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def get_uid(self, username: str) -> str:
        """Returns the ID of a specific user"""
        if self._uid_cache.get(username) is not None:
            return self._uid_cache[username]
        uid = str(super(InstagramAPI, self).user_id_from_username(username))
        self._uid_cache[username] = uid
        return uid

    @api_func("following")
    def get_following(self, username: str) -> List[UserShort]:
        """Get all the users that a specific user is following"""
        uid = self.get_uid(username)
        users = super(InstagramAPI, self).user_following(uid).values()
        return users

    @api_func("followers")
    def get_followers(self, username: str) -> List[UserShort]:
        """Get all the followers of a specific user"""
        uid = self.get_uid(username)
        users = super(InstagramAPI, self).user_followers(uid).values()
        return users

    @api_func("userinfo")
    def get_userinfo(self, username: str) -> User:
        """Gets information about a user"""
        uid = self.get_uid(username)
        return super(InstagramAPI, self).user_info(uid)

    @api_func("login", json_response=False)
    def login(self, username: str, pwd: str) -> Tuple[int, str]:
        """Authenticate using the Instagram v1 mobile API"""
        try:
            status = super(InstagramAPI, self).login(username, pwd)
        except Exception as e:
            return 1, str(e)
        return 0, "success"

    def as_json(self, obj: Any, fields: List[str] = None) -> Dict[str, Any]:
        """Form a JSON response to be returned through the proxy server"""
        data = {}
        if obj is None:
            return obj
        if fields is None:
            fields = []
            for attr in dir(obj):
                try:
                    value = getattr(obj, attr)
                except AttributeError:
                    continue
                if type(value) == type(obj) or isinstance(obj, int): # prevent infinite recursion
                    continue
                if not callable(value) and not attr.startswith("_"):
                    fields.append(attr)
        if not fields:
            return obj
        for field in fields:
            value = getattr(obj, field, None)
            data[field] = self.as_json(value, fields=None)
        return data


client = InstagramAPI()

def execute(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        func, do_json = funcmap.get(command["function"], (None, False))
        assert func is not None
        kwargs = command["kwargs"]
        kwargs["self"] = client
        result = func(**kwargs)
        if do_json:
            result = client.as_json(result, command.get("fields"))
            result["status"] = "success"
            return result
        return {"status": "success", "raw": str(result), "response": {}}

    except KeyError:
        return {"status": "error", "reason": "command missing key 'kwargs'"}
    
    except AssertionError:
        return {"status": "error", "reason": f"function {command['function']!r} not found"}
    
    except Exception as e:
        return {"status": "error", "reason": str(e)[0].lower() + str(e)[1:]}

def execute_via_proxy(command: Dict[str, Any], localhost: bool = False) -> Dict[str, Any]:
    if localhost:
        proxyurl = "http://localhost:9102/service"
    else:
        proxyurl = "https://instagram-automation-sand.vercel.app/service"
    data = {"auth": os.getenv("PROXYSERVER_AUTH_KEY"), "command": command}
    proxy_resp = requests.post(url=proxyurl, json=data)
    if not proxy_resp.ok:
        raise Exception(
            "could not reach proxy server"
        )
    json_resp = proxy_resp.json()
    if json_resp["status"] == "error":
        raise Exception(
            f"received bad response from proxy server: {json_resp}"
        )
    else:
        api_resp = json_resp["api_response"]
        return api_resp
