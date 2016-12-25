import websocket

import tty
import termios
from threading import Thread
from sys import stdout, stdin
from copy import copy


def connect_and_auth(url, password) -> websocket.WebSocket:
    ws = websocket.create_connection(url, timeout=0.5)
    frame = ws.recv_frame()

    if frame.data != b"Password: ":
        raise Exception("Unexpected response: {}".format(frame.data))
    stdout.write(frame.data.decode('utf-8'))
    ws.send(password + "\n")

    frame = ws.recv_frame()
    if frame.data.strip() != b"WebREPL connected\r\n>>>":
        raise Exception("Unexpected response: {}".format(frame.data))
    return ws


def do_eval(args):
    ws = connect_and_auth(args.WEBSOCKET[0], args.password)
    ws.send("\x02")
    stdout.write(read_until_eval_or_timeout(ws))
    ws.send(args.CODE[0] + "\r\n")

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


def do_repl(args):
    print("Type ^[ CTRL-] or CTRL-D to quit")
    ws = connect_and_auth(args.WEBSOCKET[0], args.password)
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


def do_put(args):
    raise NotImplementedError()


def do_get(args):
    raise NotImplementedError()
