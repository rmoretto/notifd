from multiprocessing.connection import Client
import json

import click


def send_ipc_message(message):
    address = ("localhost", 56789)
    conn = Client(address, authkey=b"notify-history")
    conn.send(message)

    response = conn.recv()
    conn.close()

    return response


@click.group()
def cli():
    pass


@cli.command()
@click.argument("id")
def pop(id):
    response = send_ipc_message({"command": "pop", "data": {"id": id}})
    print(json.dumps(response, ensure_ascii=False))


@cli.command()
def clear():
    response = send_ipc_message({"command": "clear"})
    print(json.dumps(response, ensure_ascii=False))

@cli.command()
def list():
    response = send_ipc_message({"command": "list"})
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    cli()
