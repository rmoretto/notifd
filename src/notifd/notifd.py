import json
import os
import string
import random
import traceback
from pathlib import Path
from pprint import pp
from datetime import datetime
from multiprocessing.connection import Listener
from threading import Thread

import click
import dbus
import gi
from PIL import Image

gi.require_version("Gtk", "3.0")

from gi.repository import Gio, GLib, Gtk
from dbus.mainloop.glib import DBusGMainLoop

IPC_HOST = "localhost"
IPC_PORT = 56789

BASE_FOLDER = "/tmp/notify-listener"
IMAGE_DATA_FOLDER = f"{BASE_FOLDER}/image-datas"
NOTIFICATIONS_DATA_FILE = f"{BASE_FOLDER}/notifications.json"
GLOBAL_STATE_FILE = f"{BASE_FOLDER}/global_state.json"
NOTIFICATION_DATA = {}

NOTIFY_RULES = {
    "interface": "org.freedesktop.Notifications",
    "member": "Notify",
    "eavesdrop": "true",  # https://bugs.freedesktop.org/show_bug.cgi?id=39450
}


def fetch_global_state():
    global_state_path = Path(GLOBAL_STATE_FILE)
    return json.loads(global_state_path.read_text())


def set_global_state(data):
    global_state_path = Path(GLOBAL_STATE_FILE)
    global_state_path.write_text(json.dumps(data))


def fetch_notifications_state():
    notification_data_path = Path(NOTIFICATIONS_DATA_FILE)
    return json.loads(notification_data_path.read_text())


def set_notifications_state(data):
    notification_data_path = Path(NOTIFICATIONS_DATA_FILE)
    notification_data_path.write_text(json.dumps(data))


def handle_ipc_message(message):
    command = message.get("command")
    if command == "pop":
        return pop_history(message)
    elif command == "clear":
        return clear_history()
    elif command == "list":
        return list_history()
    elif command == "get_notifications_read":
        return get_notifications_read()
    elif command == "set_notifications_read":
        return set_notifications_read()
    elif command == "get_notifications_read":
        return get_notifications_read()

    else:
        return {"error": "invalid_command", "message": f'Invalid command "{command}"'}


def pop_history(message):
    notification_id = message.get("data", {}).get("id")
    if not notification_id:
        return {
            "success": False,
            "error": "missing_id",
            "message": "Missing notification id",
        }

    notification_data = fetch_notifications_state()

    try:
        notification_data.pop(notification_id)
    except KeyError:
        return {
            "success": False,
            "error": "invalid_id",
            "message": f'Notification with ID "{notification_id}" not found',
        }

    set_notifications_state(notification_data)
    return {
        "success": True,
        "message": f'Notification with ID "{notification_id}" deleted',
    }


def clear_history():
    set_notifications_state({})

    return {"success": True, "message": "Notification history cleared"}


def list_history():
    notification_data = fetch_notifications_state()

    data = sorted(
        notification_data.values(), key=lambda i: i["timestamp"], reverse=True
    )

    return {"success": True, "data": data}


def set_notifications_read():
    global_state_data = fetch_global_state()
    global_state_data["notifications_read"] = True
    set_global_state(global_state_data)

    return {"success": True, "message": f"Notifications set as read successfully"}


def get_notifications_read():
    global_state_data = fetch_global_state()

    return {
        "success": True,
        "data": {"notifications_read": global_state_data["notifications_read"]},
    }


def ipc_main_loop(conn):
    while True:
        try:
            request = conn.recv()
        except EOFError:
            return
        print("received data", request)
        response = handle_ipc_message(request)
        conn.send(response)


def run_ipc_server(ipc_host, ipc_port):
    address = (ipc_host, ipc_port)
    print(f"Initializing IPC Listener at {address}")
    listener = Listener(address, authkey=b"notify-history")
    while True:
        conn = listener.accept()
        ipc_main_loop(conn)


def init_ipc_server(ipc_host, ipc_port):
    thread = Thread(target=run_ipc_server, args=(ipc_host, ipc_port), daemon=True)
    thread.start()


def save_image_data(notification_id, image_data):
    if not image_data:
        return

    has_alpha = image_data[3]
    mode = "RGB"
    if has_alpha:
        mode = "RGBA"

    img_w, img_h = int(image_data[0]), int(image_data[1])
    img_data = bytes(image_data[6])
    img_strides = image_data[2]

    try:
        img = Image.frombytes(mode, (img_w, img_h), img_data, "raw", mode, img_strides)
    except Exception as exc:
        print("Error creating image from image-data: ", exc)
        print(traceback.format_exc())
        return

    image_path = f"{IMAGE_DATA_FOLDER}/{notification_id}.png"
    with open(image_path, "wb") as f:
        img.save(f, format="png")

    return image_path


def get_icon_path(desktop_entry):
    if not desktop_entry:
        return

    icon_theme = Gtk.IconTheme.get_default()
    image_file = None

    icon = Gio.content_type_get_icon(desktop_entry).to_string().split()
    icon_normalized = (
        Gio.content_type_get_icon(desktop_entry.lower()).to_string().split()
    )
    icons_search = set(icon + icon_normalized)

    for entry in icons_search:
        if entry == "." or entry == "GThemedIcon":
            continue

        try:
            image_file = icon_theme.lookup_icon(entry, 32, 0).get_filename()
            if image_file:
                return image_file
        except Exception as exc:
            print(f'Failed to get icon "{desktop_entry}" from {entry}: {str(exc)}')


def create_random_id():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=10))


def generate_args_dict(arg_list):
    now = datetime.now()
    timestamp = now.timestamp()

    appname = str(arg_list[0])
    id = int(arg_list[1])

    summary = str(arg_list[3])
    body = str(arg_list[4])

    if id == 0:
        id = create_random_id()
    else:
        id = str(id)

    notification_data = arg_list[6]
    desktop_entry = None
    try:
        desktop_entry = notification_data["desktop-entry"]
    except KeyError:
        pass

    urgency = "low"
    try:
        urgency_byte = arg_list[6]["urgency"]
        if int(urgency_byte) == 0:
            urgency = "low"
        elif int(urgency_byte) == 1:
            urgency = "normal"
        elif int(urgency_byte) == 2:
            urgency = "critical"
    except (IndexError, KeyError):
        pass

    # Check for the image-path first
    icon_path = notification_data.get("image-path")
    # If image-path is not available get the image-date and create a png image
    if not icon_path:
        icon_path = save_image_data(id, notification_data.get("image-data"))
    # Try to the desktop entry icon
    if not icon_path and desktop_entry:
        icon_path = get_icon_path(desktop_entry)

    return {
        "id": id,
        "appname": appname,
        "desktop_entry": desktop_entry,
        "summary": summary,
        "body": body,
        "icon_path": icon_path,
        "urgency": urgency,
        "timestamp": timestamp,
    }


def notification_callback(_, message):
    if type(message) != dbus.lowlevel.MethodCallMessage:
        return

    notification_data = fetch_notifications_state()

    args_list = message.get_args_list()
    try:
        notification = generate_args_dict(args_list)
    except Exception as exc:
        print(f"Error on generate_args_dict: {str(exc)}")
        print(traceback.format_exc())
        return

    print("Received notification:")
    pp(notification)

    notification_data[notification["id"]] = notification
    set_notifications_state(notification_data)

    global_state_data = fetch_global_state()
    global_state_data["notifications_read"] = False
    set_global_state(global_state_data)


def initialize_folders_and_data():
    try:
        os.mkdir(BASE_FOLDER)
    except FileExistsError:
        pass

    try:
        os.mkdir(IMAGE_DATA_FOLDER)
    except FileExistsError:
        pass

    notification_data_path = Path(NOTIFICATIONS_DATA_FILE)
    if not notification_data_path.exists():
        notification_data_path.write_text("{}")

    global_state_path = Path(GLOBAL_STATE_FILE)
    if not global_state_path.exists():
        global_state_path.write_text('{"notifications_read": true}')


@click.group()
def main():
    pass


@main.command()
@click.option("--ipc-host", default=IPC_HOST, show_default=True)
@click.option("--ipc-port", default=IPC_PORT, type=int, show_default=True)
def run(ipc_host, ipc_port):
    init_ipc_server(ipc_host, ipc_port)
    initialize_folders_and_data()

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus.add_match_string(
        ",".join([f"{key}={value}" for key, value in NOTIFY_RULES.items()])
    )
    bus.add_message_filter(notification_callback)

    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        bus.close()


if __name__ == "__main__":
    main()
