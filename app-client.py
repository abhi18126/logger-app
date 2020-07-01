#!/usr/bin/python3.6

import socket
import selectors
import traceback
import configparser
import psutil
import time

import libclient

sel = selectors.DefaultSelector()
config = configparser.ConfigParser()
config.read('config.ini')


def create_request(value, clientId):
        return dict(
            type="text/json",
            encoding="utf-8",
            clientId=clientId,
            content=dict(value=value, clientId=clientId),
        )


def start_connection(host, port, request):
    addr = (host, port)
    print("starting connection to", addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = libclient.Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)


def get_process_data():
    data = [(proc.pid,proc.name()) for proc in psutil.process_iter()]
    print(dict(data))
    return dict(data)


def get_client_id():
    # some logic for identifying client
    return 'd12345644DD';


host, port = config['server-client']['client-ip'], int(config['server-client']['server-port'])

def collect_and_send():
    value = get_process_data()
    request = create_request(value, get_client_id())
    start_connection(host, port, request)

    try:
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                message = key.data
                try:
                    message.process_events(mask)
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}",
                    )
                    message.close()
            # Check for a socket being monitored to continue.
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == "__main__":
    while True:
        collect_and_send();
        time.sleep(5)

