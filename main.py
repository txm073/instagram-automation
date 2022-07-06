import sys
import argparse
import getpass
import shlex
import json
import time
import random
from pprint import pprint
from typing import List, Dict, Any

from igscraper import api


def call(api_cmd: Dict[str, Any], use_proxy: bool, args: argparse.Namespace) -> Dict[str, Any]:
    """Call an API command either directly or via the proxy server"""
    if args.random_delay:
        time.sleep(random.randint(5, 20))
    else:
        time.sleep(args.delay)
    if args.verbose and api_cmd["function"] != "login":
        print("api command:", api_cmd)
    if use_proxy:
        resp = api.execute_via_proxy(api_cmd)
    else:
        resp = api.execute(api_cmd)
    assert resp["status"] == "success", resp["reason"]
    return resp

def compare_users(args: argparse.Namespace) -> None:
    """Compare the data in two JSON files"""
    assert args.input, "provide two files to compare"
    with open(args.input[0], "r") as f1, open(args.input[1], "r") as f2:
        users1, users2 = json.load(f1), json.load(f2)
    if isinstance(users1, dict) and users1.get("users"):
        users1 = users1["users"]
    if isinstance(users2, dict) and users2.get("users"):
        users2 = users2["users"]
    print(f"sorting with compare mode {args.compare_mode!r}...")
    # Compare by IDs
    user1_ids = [user["pk"] for user in users1]
    user2_ids = [user["pk"] for user in users2]

    if args.compare_mode == "both":
        output_users = [user for user in users1 if user["pk"] in user2_ids]
    elif args.compare_mode == "only-first":
        output_users = [user for user in users1 if user["pk"] not in user2_ids]
    else:
        output_users = [user for user in users2 if user["pk"] not in user1_ids]
    
    data = {"compare-mode": args.compare_mode, "input-files": args.input, "users": output_users}
    if args.output:
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
    else:
        pprint(data)

def get_data(cmd: str, args: argparse.Namespace, use_proxy: bool) -> None:
    """Fetch follower/following data from the API"""
    assert args.username, "provide a username"
    if args.verbose:
        print(f"checking to see if {args.username!r} is private...")
    is_private_cmd = {"function": "userinfo", "kwargs": {"username": args.username}, "fields": ["is_private", "follower_count", "following_count"]}
    userinfo = call(is_private_cmd, use_proxy, args)
    assert (not userinfo["response"]["is_private"] or args.username == api.client._auth_user), f"cannot get information: user {args.username!r} is private"
    
    if args.verbose:
        print("username is valid, retrieving information...")

    print("retrieving data, this may take a while...")
    if cmd == "following":
        api_cmd = {"function": "following", "kwargs": {"username": args.username}}
        # The data must be gathered all at once
        users = call(api_cmd, use_proxy, args)["response"]
    else:
        # User followers endpoint supports buffered requests
        total = int(userinfo["response"]["follower_count"])
        chunksize = int(total * 0.15) + 1
        if chunksize < 100:
            chunksize = 100

        api_cmd = {"function": "followers", "kwargs": {"username": args.username, "amount": chunksize, "maxid": ""}}
        users = []
        maxid = ""
        chunks = 1
        while (maxid is not None):
            start = time.time()
            resp = call(api_cmd, use_proxy, args)
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
        resp = call(api_cmd, use_proxy, args)
        _, user_chunk = resp["response"]
        users.extend(user_chunk)

    if api_cmd["kwargs"].get("self"):
        api_cmd["kwargs"].pop("self")
    data = {"command": api_cmd, "target_user": userinfo, "users": users}

    if args.output:
        print(f"saving data to {args.output!r}")
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
    else:
        pprint(data, indent=2)

def process_args(parser: argparse.ArgumentParser, args: argparse.Namespace, use_proxy: bool = True) -> None:
    """Process the arguments entered by the user"""
    if args.output:
        assert args.output.endswith(".json"), "output file must be JSON"
    if args.use_proxy:
        use_proxy = True
        
    cmd = args.command[0].lower().strip()
    if cmd == "login":
        if args.credentials:
            with open(args.credentials, "w") as f:
                data = json.load(f)
            username = data["username"]
            pwd = data["password"]
        else:    
            username = input("username: ")
            if args.show_pwd:
                pwd = input("password: ")
            else:
                pwd = getpass.getpass("password: ")
        api_cmd = {"function": "login", "kwargs": {"username": username, "pwd": pwd}}
        resp = call(api_cmd, use_proxy, args)
        raw_response = eval(resp["raw"])
        assert raw_response[0] == 0, raw_response[1]
        print(f"successfully logged in as {username!r}")

    elif cmd in ("following", "followers"):
        get_data(cmd, args, use_proxy)

    elif cmd == "compare":
        compare_users(args)

    elif cmd == "help":
        helpstr = parser.format_help()
        print(helpstr)

    elif cmd == "exit":
        print("exiting...")
        sys.exit(0)

    else:
        raise Exception(
            f"invalid command {cmd!r}"
        )        

def run_interactive(parser: argparse.ArgumentParser) -> None:
    """Interactive shell (used for when you want to access the API directly, rather than via the proxy server)"""
    print("running interactive shell...")
    while True:
        try:
            cmd = input("\n" + parser.prog + ">")
            argv = shlex.split(cmd)
            args = parser.parse_args(argv)
            process_args(parser, args, use_proxy=False)
        except (EOFError, KeyboardInterrupt):
            print("\nexiting...")
            break 
        except Exception as e:
            print("error:", str(e))

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="igapi", description="interact with the Instagram mobile API")
    parser.add_argument("command", nargs=1, help="the command to be executed")
    parser.add_argument("-u", "--username", action="store", type=str, nargs="?", metavar="<username>", help="the username to be passed")
    parser.add_argument("-o", "--output", action="store", type=str, nargs="?", metavar="<output-file>", help="pipe the output to a JSON file")
    parser.add_argument("-i", "--input", action="store", type=str, nargs=2, metavar="<input-files>", help="compare data in two JSON files")
    parser.add_argument("-v", "--verbose", action="store_true", help="display additional information")
    parser.add_argument("--show-pwd", action="store_true", help="show password as it is being inputted")
    parser.add_argument("-d", "--delay", action="store", type=int, default=1, metavar="<delay>", help="the delay between API calls (in seconds)")
    parser.add_argument("--random-delay", action="store_true", help="add a random amount of delay between API calls")
    parser.add_argument("--compare-mode", action="store", type=str, metavar="<compare-mode>", choices=["only-first", "only-second", "both"], help="which way to compare two data files")
    parser.add_argument("-c", "--credentials", action="store", type=str, metavar="<credentials>", nargs="?", help="JSON file storing login credentials")
    parser.add_argument("-p", "--proxy", action="store_true", help="indicate whether to run commands via a proxy server")

    if "--local" in argv:
        return run_interactive(parser)
    args = parser.parse_args(parser, argv[1:])
    try:
        process_args(args, use_proxy=True)
    except Exception as e:
        print("error:", str(e))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
