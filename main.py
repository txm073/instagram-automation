import sys
import argparse
import getpass
import shlex
import json
import time
from pprint import pprint
from typing import List, Dict, Any

from tqdm import tqdm
import api


def _call(api_cmd: Dict[str, Any], use_proxy: bool, verbose: bool = False) -> Dict[str, Any]:
    if verbose and api_cmd["function"] != "login":
        print("api command:", api_cmd)
    if use_proxy:
        resp = api.execute_via_proxy(api_cmd, localhost=True)
    else:
        resp = api.execute(api_cmd)
    assert resp["status"] == "success", resp["reason"]
    return resp

def process_args(args: argparse.Namespace, use_proxy: bool = True) -> None:
    if args.output:
        assert args.output.endswith(".json"), "output file must be JSON"

    cmd = args.command[0].lower().strip()
    if cmd == "login":
        username = input("username: ")
        if args.show_pwd:
            pwd = input("password: ")
        else:
            pwd = getpass.getpass("password: ")
        api_cmd = {"function": "login", "kwargs": {"username": username, "pwd": pwd}}
        resp = _call(api_cmd, use_proxy, args.verbose)
        raw_response = eval(resp["raw"])
        assert raw_response[0] == 0, raw_response[1]
        pprint(resp)

    elif cmd in ("following", "followers"):
        assert args.username, "provide a username"
        if args.verbose:
            print(f"checking to see if {args.username!r} is private...")
        is_private_cmd = {"function": "userinfo", "kwargs": {"username": args.username}, "fields": ["is_private", "follower_count", "following_count"]}
        userinfo = _call(is_private_cmd, use_proxy, args.verbose)
        assert (not userinfo["response"]["is_private"] or args.username == api.client._auth_user), f"cannot get information: user {args.username!r} is private"
        
        if args.verbose:
            print("username is valid, retrieving information...")
            print("estimated time to receive data: ")
        total = int(userinfo["response"]["follower_count"] if cmd == "followers" else userinfo["response"]["following_count"])
        chunksize = int(total * 0.15) + 1
        if chunksize < 100:
            chunksize = 100
        #print(f"{total=}, {chunksize=}, {remainder=}, {n_chunks=}")
        api_cmd = {"function": cmd, "kwargs": {"username": args.username, "amount": chunksize, "maxid": ""}}
        users = []
        maxid = ""
        chunks = 1
        while (maxid is not None):
            start = time.time()
            #print(f"chunk {i + 1} / {n_chunks}")
            resp = _call(api_cmd, use_proxy, False)
            maxid, user_chunk = resp["response"]
            actual_chunksize = len(user_chunk)
            n_chunks = total / actual_chunksize
            users.extend(user_chunk)
            api_cmd["kwargs"]["maxid"] = maxid
            elapsed = time.time() - start
            if actual_chunksize == chunksize:
                print(f"received chunk {chunks}, estimated completetion time: {n_chunks * elapsed * (1 - chunks / n_chunks):2f}s")
            chunks += 1
        print("receiving remaining data...")
        resp = _call(api_cmd, use_proxy, False)
        _, user_chunk = resp["response"]
        users.extend(user_chunk)
        #print(len(users), total)

        if args.output:
            print(f"saving data to {args.output!r}")
            with open(args.output, "w") as f:
                json.dump(users, f, indent=2)
        else:
            pprint(users, indent=2)

    else:
        raise Exception(
            f"invalid command {cmd!r}"
        )        

def run_interactive(parser: argparse.ArgumentParser) -> None:
    print("running interactive shell...")
    while True:
        try:
            cmd = input("\n" + parser.prog + ">")
            argv = shlex.split(cmd)
            args = parser.parse_args(argv)
            process_args(args, use_proxy=False)
        except (EOFError, KeyboardInterrupt):
            print("\nexiting...")
            break 
        except Exception as e:
            print("error:", str(e))

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="igapi", description="interact with the Instagram mobile API")
    parser.add_argument("command", nargs=1, help="the command to be executed")
    parser.add_argument("-u", "--username", action="store", nargs="?", metavar="<username>", help="the username to be passed")
    parser.add_argument("-o", "--output", action="store", nargs="?", metavar="<output-file>", help="pipe the output to a file")
    parser.add_argument("-v", "--verbose", action="store_true", help="display additional information")
    parser.add_argument("--show-pwd", action="store_true", help="show password as it is being inputted")

    if "--local" in argv:
        return run_interactive(parser)
    args = parser.parse_args(argv[1:])
    try:
        process_args(args, use_proxy=True)
    except Exception as e:
        print("error:", str(e))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
