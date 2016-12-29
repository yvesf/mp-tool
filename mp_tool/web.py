"""
Implementation of commands that run against the websocket interface of micropython
"""
from . import Constants

import websocket

import tty
import termios
from threading import Thread
from sys import stdout, stdin
from copy import copy
import os
import struct


def _connect_and_auth(url: str, password: str) -> websocket.WebSocket:
    ws = websocket.create_connection(url, timeout=0.5)
    frame = ws.recv_frame()

    if password is None:
        stdout.write('Password: ')
        stdout.flush()
        password = stdin.readline()

    if frame.data != b"Password: ":
        raise Exception("Unexpected response: {}".format(frame.data))
    ws.send(password + "\n")

    frame = ws.recv_frame()
    if frame.data.strip() != b"WebREPL connected\r\n>>>":
        raise Exception("Unexpected response: {}".format(frame.data))
    return ws


def get(url: str, password: str, remote_filename: str, target: str):
    if target:
        if os.path.isdir(target):
            local_filename = os.path.join(target, os.path.basename(remote_filename))
        else:
            local_filename = target
    else:
        local_filename = os.path.basename(remote_filename)

    remote_filename_b = remote_filename.encode('utf-8')

    ws = _connect_and_auth(url, password)
    ws.settimeout(5)

    rec = struct.pack(Constants.WEBREPL_REQ_S, b"WA",
                      Constants.WEBREPL_GET_FILE, 0, 0, 0,
                      len(remote_filename_b), remote_filename_b)

    ws.send(rec, websocket.ABNF.OPCODE_BINARY)

    frame = ws.recv_frame()
    sig, code = struct.unpack("<2sH", frame.data)
    if frame.opcode != websocket.ABNF.OPCODE_BINARY or sig != b'WB' or code != 0:
        raise Exception("Error initial response sig={} code={}".format(sig, code))

    ret = b""
    while True:
        # Confirm message
        ws.send(b"\1", websocket.ABNF.OPCODE_BINARY)
        frame = ws.recv_frame()
        print(frame)
        (sz,) = struct.unpack("<H", frame.data[:2])
        if sz == 0:
            break
        ret += frame.data[2:]

    frame = ws.recv_frame()
    sig, code = struct.unpack("<2sH", frame.data)
    if frame.opcode != websocket.ABNF.OPCODE_BINARY or sig != b'WB' or code != 0:
        raise Exception("Error final response sig={} code={}".format(sig, code))

    with open(local_filename, 'wb') as fh:
        fh.write(ret)


def put(url: str, password: str, local_filename: str, target: str):
    if target:
        remote_filename = os.path.join(target, local_filename)
    else:
        remote_filename = os.path.basename(local_filename)
    remote_filename_b = remote_filename.encode('utf-8')

    with open(local_filename, 'br') as file_fh:
        data = file_fh.read()

    ws = _connect_and_auth(url, password)
    ws.settimeout(5)

    sz = len(data)
    rec = struct.pack(Constants.WEBREPL_REQ_S, b"WA",
                      Constants.WEBREPL_PUT_FILE, 0, 0, sz,
                      len(remote_filename_b), remote_filename_b)

    ws.send(rec[:10], websocket.ABNF.OPCODE_BINARY)
    ws.send(rec[10:], websocket.ABNF.OPCODE_BINARY)

    frame = ws.recv_frame()
    sig, code = struct.unpack("<2sH", frame.data)
    if frame.opcode != websocket.ABNF.OPCODE_BINARY or sig != b'WB' or code != 0:
        raise Exception("Error initial response sig={} code={}".format(sig, code))

    i = 0
    n = int(sz / 256) + 1
    print("{}..{}: ".format(i, n), end="")
    cnt = 0
    while True:
        buf = data[cnt:cnt + 256]
        if not buf:
            break
        ws.send(buf, websocket.ABNF.OPCODE_BINARY)

        cnt += len(buf)
        i += 1
        print("{} ".format(i), end="")
    print(". done")

    frame = ws.recv_frame()
    sig, code = struct.unpack("<2sH", frame.data)
    if frame.opcode != websocket.ABNF.OPCODE_BINARY or sig != b'WB' or code != 0:
        raise Exception("Error initial response sig={} code={}".format(sig, code))


def eval(url: str, password: str, code: str):
    ws = _connect_and_auth(url, password)
    ws.send(Constants.ENTER_REPL_MODE)
    stdout.write(read_until_eval_or_timeout(ws))
    ws.send(code + "\r\n")

    result = read_until_eval_or_timeout(ws)
    stdout.write(result[:-6])
    print("")
    ws.close()


def read_until_eval_or_timeout(ws: websocket.WebSocket):
    buf = ""
    while not buf.endswith("\r\n>>> "):
        buf += ws.recv()
    return buf


class Reader(Thread):
    def __init__(self, ws):
        Thread.__init__(self)
        self.ws = ws
        self.stop = False

    def run(self):
        while True:
            try:
                frame = self.ws.recv_frame()
                stdout.write(frame.data.decode('utf-8'))
                stdout.flush()
            except Exception as e:
                if self.stop:
                    break


def set_tty_raw_mode(fd):
    saved_mode = termios.tcgetattr(fd)

    new_mode = copy(saved_mode)
    new_mode[tty.LFLAG] = new_mode[tty.LFLAG] & ~termios.ECHO
    new_mode[tty.CC][tty.VMIN] = 1
    new_mode[tty.CC][tty.VTIME] = 0
    set_tty_mode(fd, new_mode)

    return saved_mode


def set_tty_mode(fd, mode):
    termios.tcsetattr(fd, termios.TCSAFLUSH, mode)


def repl(url: str, password: str = None):
    print("Type ^[ CTRL-] or CTRL-D to quit")
    ws = _connect_and_auth(url, password)
    ws.send("\x02")

    reader = Reader(ws)
    reader.start()

    saved_tty_mode = set_tty_raw_mode(stdin.fileno())
    try:
        tty.setraw(stdin.fileno())
        while True:
            try:
                in_char = stdin.read(1)
                if in_char == "\x1d" or in_char == "\x04":  # escape char 'Ctrl-]' or CTRL-C
                    break
                else:
                    ws.send(in_char)
            except KeyboardInterrupt:
                break
    except Exception as _:
        pass

    reader.stop = True
    ws.close()

    set_tty_mode(stdin.fileno(), saved_tty_mode)
    print("")
