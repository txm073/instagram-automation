import json
import os, sys
import logging
import warnings
from pprint import pprint
from typing import (
    List, 
    Tuple, 
    Dict, 
    Any, 
    Callable,
    TypeVar,
    Union,
    NoReturn
)
from instagrapi import Client
from instagrapi.types import User, UserShort
import requests

logging.getLogger("instagrapi").disabled = True
logging.getLogger("public_request").disabled = True
warnings.warn(
    "use of the Instagram v1 mobile API is not recommended as it is deprecated",
    DeprecationWarning
)
warnings.warn(
    "use of this API may result in your account being temporarily banned", 
    UserWarning
)

funcmap: Dict[str, Tuple[Callable, bool]] = {}


def _is_builtin_type(obj: Any) -> bool:
    return obj is None or isinstance(obj, ( 
        int, float, bool, complex, bytearray, memoryview, str, 
        bytes, slice, range, list, dict, set, type, super, staticmethod, classmethod
    ))

def api_func(funcname: str, jsonify: bool = True) -> Callable:
    def wrapper(fn) -> Callable:
        funcmap[funcname] = (fn, jsonify)
        def inner(*args, **kwargs) -> Any:
            result = fn(*args, **kwargs)
            return result
        return inner
    return wrapper


class InstagramAPI(Client):
    _inst: type = None
    _uid_cache: Dict[str, str] = {}
    _auth_user: str = None
    _default_attribute = type("DefaultAttribute", (), {})

    def __new__(cls, *args, **kwargs) -> Any:
        """Method override to ensure that only one instance of the class is created"""
        if cls._inst is None:
            cls._inst = super(InstagramAPI, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self, *args, **kwargs) -> NoReturn:
        """Create user information cache file if it does not exist"""
        self._cache_data = True
        if not os.path.exists("cache.json"):
            try:
                with open("cache.json", "w") as f:
                    json.dump({"users": []}, f)
            except OSError as e:
                self._cache_data = False
        super(InstagramAPI, self).__init__(*args, **kwargs)

    def get_uid(self, username: str) -> str:
        """Returns the ID of a specific user"""
        if self._uid_cache.get(username) is not None:
            return self._uid_cache[username]
        uid = str(super(InstagramAPI, self).user_id_from_username(username))
        self._uid_cache[username] = uid
        return uid

    def _cache(self, obj: Dict[str, Any]) -> None:
        if not self._cache_data:
            return None
        if os.path.exists("cache.json"):
            with open("cache.json", "r") as f:
                contents = json.load(f)
        else:
            contents = {"users": []}
        contents["users"].append(obj)
        with open("cache.json", "w") as f:
            json.dump(contents, f, indent=2)

    def _lookup(self, value, by="uid") -> Union[None, Dict[str, Any]]:
        if not self._cache_data:
            return None
        if not os.path.exists("cache.json"):
            return None
        with open("cache.json", "r") as f:
            contents = json.load(f)
        by = by.replace("uid", "pk")
        for user in contents["users"]:
            if user.get(by) == value:
                return user
        return None

    @api_func("following")
    def get_following(self, username: str) -> List[UserShort]:
        """Get all the users that a specific user is following"""
        uid = self.get_uid(username)
        users = super(InstagramAPI, self).user_following_v1(uid, 0)
        return users

    @api_func("followers")
    def get_followers_chunk(self, username: str, amount: int, maxid: str) -> Tuple[str, List[UserShort]]:
        """Get the followers of a specific user"""
        uid = self.get_uid(username)
        users, max_id = super(InstagramAPI, self).user_followers_v1_chunk(uid, amount, maxid)
        return [max_id, users]

    @api_func("userinfo", jsonify=False)
    def get_userinfo(self, username: str) -> Dict[str, Any]:
        """Gets information about a user"""
        cached = self._lookup(username, by="username")
        if cached:
            return cached
        uid = self.get_uid(username)
        info = self.as_json(super(InstagramAPI, self).user_info(uid))

        self._cache(info)
        return info

    @api_func("login", jsonify=False)
    def login(self, username: str, pwd: str) -> Tuple[int, str]:
        """Authenticate using the Instagram v1 mobile API"""
        try:
            status = super(InstagramAPI, self).login(username, pwd, True)
        except Exception as e:
            return 1, str(e)
        self._auth_user = username
        return 0, "success"

    def as_json(self, obj: Any, fields: List[str] = None, rlevel: int = 0) -> Dict[str, Any]:
        """Form a JSON response to be returned through the proxy server"""
        if isinstance(obj, (set, tuple)):
            obj = list(obj)
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self.as_json(value, fields=fields if not rlevel else None, rlevel=rlevel + 1)    
        elif isinstance(obj, list):
            for i in range(len(obj)):
                obj[i] = self.as_json(obj[i], fields=fields if not rlevel else None, rlevel=rlevel + 1)
        if not hasattr(obj, "__dict__"):
            return obj

        result = {}
        if fields is None:
            fields = obj.__dict__.items()
        else:
            values = []
            for f in fields:
                val = getattr(obj, f, self._default_attribute())
                if isinstance(val, self._default_attribute): # attribute does not exist
                    continue
                values.append(val)
            fields = zip(fields, values)
        for key, val in fields:
            if key.startswith("_") or callable(val):
                continue
            result[key] = self.as_json(val, rlevel=rlevel + 1)
        return result


client = InstagramAPI()

def execute(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        func, do_json = funcmap.get(command["function"], (None, False))
        assert func is not None
        kwargs = command["kwargs"]
        kwargs["self"] = client
        result = func(**kwargs)
        if do_json:
            result = {"response": result}
            result = client.as_json(result, command.get("fields"))
            result["status"] = "success"
            return result
        if isinstance(result, dict):
            return {"status": "success", "response": result}
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
