class Constants:
    ENTER_RAW_MODE = b'\x01'  # CTRL-A
    ENTER_REPL_MODE = b'\x02'  # CTRL-B
    INTERRUPT = b'\x03'  # CTRL-C
    CTRL_D = b'\x04'  # CTRL-D
    MARKER_BEGIN = b'>>>>>>>>>>'
    MARKER_END = b'<<<<<<<<<<'

    WEBREPL_REQ_S = "<2sBBQLH64s"
    WEBREPL_PUT_FILE = 1
    WEBREPL_GET_FILE = 2
    WEBREPL_GET_VER = 3
