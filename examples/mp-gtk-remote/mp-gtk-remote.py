#!/usr/bin/env python3
from mp_tool import web

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def send_signal(sender):
    value = int(entry_number.get_value())
    web.eval(entry_host.get_text(),
            entry_password.get_text(),
	    "set_value({})\r\n".format(repr(value)))


win = Gtk.Dialog(default_width=1100, default_height=200)
win.connect("delete-event", Gtk.main_quit)
vbox = win.get_content_area()

entry_host = Gtk.Entry(text='ws://esp_licht:8266')
vbox.pack_start(entry_host, True, False, 0)

entry_password = Gtk.Entry(text='password')
vbox.pack_start(entry_password, True, False, 0)

entry_number = Gtk.Scale(
	orientation=Gtk.Orientation.HORIZONTAL, 
	adjustment=Gtk.Adjustment(0, 0, 63, 1, 10, 0),
	digits=0)
vbox.pack_start(entry_number, True, True, 0)

button = Gtk.Button("Sende Signal")
button.connect("clicked", send_signal)
vbox.pack_start(button, True, True, 0)

win.show_all()
Gtk.main()

