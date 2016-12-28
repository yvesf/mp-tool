"""
Implementation of commands that run against the serial interface of micropython
"""
from . import Constants

try:
    import serial
except ImportError:
    print("Could not find pyserial library")
    raise

import os


def eval(port: str, code: str):
    with serial.Serial(port=port, baudrate=115200) as fh:
        fh.write(Constants.INTERRUPT)
        fh.write(Constants.ENTER_REPL_MODE)
        _, _ = fh.readline(), fh.readline()
        print(fh.readline().decode('utf-8').strip())
        print(fh.readline().decode('utf-8').strip())

        fh.write(code.encode('utf-8') + b"\r\n")
        fh.flush()

        buf = fh.read(1)
        i = 0
        while not buf.endswith(b"\r\n>>> "):
            buf += fh.read(1)
            i += 1
            if i > 300:
                raise Exception("Exceed number of bytes while seeking for end of output")
        print(buf.decode('utf-8')[:-6])


def ls(port: str, directory: str):
    with serial.Serial(port=port, baudrate=115200) as fh:
        fh.write(Constants.INTERRUPT)  # ctrl-c interrupt
        fh.write(Constants.ENTER_RAW_MODE)  # ctrl-a raw-mode
        fh.write(b"import os\r\n")
        fh.write(b"print()\r\n")
        fh.write(b"print('" + Constants.MARKER_BEGIN + b"')\r\n")
        fh.write(b"try:")
        fh.write(b"    print('\\n'.join(os.listdir(" + repr(directory).encode('utf-8') + b")))\r\n")
        fh.write(b"except OSError as e:\r\n")
        fh.write(b"    print(str(e))\r\n")
        fh.write(b"print('" + Constants.MARKER_END + b"')\r\n")
        fh.write(b"print()\r\n")
        fh.write(Constants.CTRL_D)
        fh.flush()
        fh.reset_input_buffer()

        _line_ok = fh.readline()
        if fh.readline().strip() != Constants.MARKER_BEGIN:
            raise Exception('Failed to find begin marker')

        line = fh.readline()
        while line.strip() != Constants.MARKER_END:
            print(line.strip().decode('utf-8'))
            line = fh.readline()

        fh.write(Constants.ENTER_REPL_MODE)


def get(port: str, remote_filename: str, target: str):
    if target:
        if os.path.isdir(target):
            local_filename = os.path.join(target, os.path.basename(remote_filename))
        else:
            local_filename = target
    else:
        local_filename = os.path.basename(remote_filename)

    with serial.Serial(port=port, baudrate=115200) as fh:
        fh.write(Constants.INTERRUPT)  # ctrl-c interrupt
        fh.write(Constants.ENTER_RAW_MODE)  # ctrl-a raw-mode
        fh.write(b"import sys\r\n")
        fh.write(b"import os\r\n")
        fh.write(b"print()\r\n")
        fh.write(b"print('" + Constants.MARKER_BEGIN + b"')\r\n")
        fh.write(b"try:\r\n")
        fh.write("   print(os.stat({})[6])\r\n".format(repr(remote_filename)).encode('utf-8'))
        fh.write(b"except OSError:\r\n")
        fh.write(b"  print('-1')\r\n")
        fh.write(b"print('" + Constants.MARKER_END + b"')\r\n")
        fh.write("with open({}, 'rb') as fh:\r\n".format(repr(remote_filename)).encode('utf-8'))
        # use sys.stdout.buffer to avoid cr to crlf conversion
        fh.write(b"    sys.stdout.buffer.write(fh.read())\r\n")
        fh.write(b"print()\r\n")
        fh.write(Constants.CTRL_D)
        fh.flush()
        fh.reset_input_buffer()

        _line_ok = fh.readline()

        if fh.readline().strip() != Constants.MARKER_BEGIN:
            raise Exception('Failed to find begin marker')

        length = int(fh.readline().strip().decode('utf-8'))
        if fh.readline().strip() != Constants.MARKER_END:
            raise Exception("Failed to read end marker value")

        if length == -1:
            raise Exception("Failed to read file {}".format(remote_filename))

        print("File length: {}".format(length))

        with open(local_filename, 'wb') as fh_out:
            bytes_processed = fh_out.write(fh.read(length))
            print("{} bytes written to {}".format(bytes_processed, local_filename))

        fh.write(Constants.ENTER_REPL_MODE)


def put(port: str, local_filename: str, target: str):
    if target:
        remote_filename = os.path.join(target, local_filename)
    else:
        remote_filename = os.path.basename(local_filename)

    with open(local_filename, 'br') as file_fh:
        data = file_fh.read()

    with serial.Serial(port=port, baudrate=115200) as fh:
        fh.write(Constants.INTERRUPT)  # ctrl-c interrupt
        fh.write(Constants.ENTER_RAW_MODE)  # ctrl-a raw-mode
        fh.write(b"import sys\r\n")
        fh.write("with open({}, 'wb') as fh:\r\n".format(repr(remote_filename)).encode('utf-8'))
        if len(data) == 0:
            fh.write(b"    pass\r\n")
        else:
            fh.write("    fh.write(sys.stdin.buffer.read({}))\r\n".format(len(data)).encode('utf-8'))
        fh.write(Constants.CTRL_D)
        fh.write(data)
        fh.write(Constants.ENTER_REPL_MODE)
