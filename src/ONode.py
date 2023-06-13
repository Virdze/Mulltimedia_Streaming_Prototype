#!/usr/bin/env python3.10

import sys
import os
import threading
import json
import socket
import time

from Server import Server
from Client import Client
from Router import Router
from Constants import *


def main() -> int:

    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <bootstrapper file> <key>", file = sys.stderr)
        return 1

    # read node's static information
    data : dict[str, dict[str, any]]

    try:
        bootstrapper = open(sys.argv[1])
        data = json.load(bootstrapper)
        bootstrapper.close()

    except Exception:
        print(f"{sys.argv[0]}: error while trying to read '{sys.argv[1]}'", file = sys.stderr)
        return 2

    neighbours : list[str]
    __type : int

    try:

        key : str = sys.argv[2]
        neighbours = data[key]['neighbours']
        __type = data[key]['type']

    except KeyError:
        print(f"{sys.argv[0]}: Value '{key}' not found in '{sys.argv[1]}'", file = sys.stderr)
        return 3

    print(neighbours)


    if __type == SERVER_TYPE:

        server = Server(neighbours)
        server.run()

    elif __type == CLIENT_TYPE:

        client = Client(neighbours)
        client.run()

    elif __type == ROUTER_TYPE:

        router = Router(neighbours)
        router.run()

    return 0


if __name__ == "__main__":
    os._exit(main())
