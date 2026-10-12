"""Authoritative Server (AS).

Listens on UDP port 53533 and handles two kinds of messages:

Registration (has VALUE and TTL):
    TYPE=A
    NAME=fibonacci.com VALUE=172.18.0.2 TTL=10

DNS query (only TYPE and NAME):
    TYPE=A
    NAME=fibonacci.com

Records are stored in a JSON file so they survive restarts.
"""
import json
import os
import socket
import threading

HOST = "0.0.0.0"
PORT = 53533
DB_FILE = os.environ.get("AS_DB_FILE", "dns_records.json")

_lock = threading.Lock()


def load_records():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_records(records):
    with open(DB_FILE, "w") as f:
        json.dump(records, f, indent=2)


def parse_message(text):
    """Turn KEY=VALUE tokens (separated by spaces or newlines) into a dict."""
    fields = {}
    for token in text.split():
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key.strip().upper()] = value.strip()
    return fields


def format_record(rtype, name, value, ttl):
    return f"TYPE={rtype}\nNAME={name} VALUE={value} TTL={ttl}\n"


def handle(message):
    fields = parse_message(message)
    rtype = fields.get("TYPE")
    name = fields.get("NAME")

    if rtype != "A" or not name:
        return "ERROR=Invalid message\n"

    # Registration request: contains VALUE and TTL
    if "VALUE" in fields and "TTL" in fields:
        with _lock:
            records = load_records()
            records[name] = {"TYPE": rtype, "VALUE": fields["VALUE"], "TTL": fields["TTL"]}
            save_records(records)
        print(f"[AS] Registered {name} -> {fields['VALUE']} (TTL={fields['TTL']})", flush=True)
        return format_record(rtype, name, fields["VALUE"], fields["TTL"])

    # DNS query: contains only TYPE and NAME
    with _lock:
        record = load_records().get(name)
    if record is None or record["TYPE"] != rtype:
        print(f"[AS] Query for unknown name {name}", flush=True)
        return f"TYPE={rtype}\nNAME={name} ERROR=NOT_FOUND\n"
    print(f"[AS] Query {name} -> {record['VALUE']}", flush=True)
    return format_record(rtype, name, record["VALUE"], record["TTL"])


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"[AS] Authoritative server listening on UDP {HOST}:{PORT}", flush=True)
    while True:
        data, addr = sock.recvfrom(2048)
        response = handle(data.decode(errors="replace"))
        sock.sendto(response.encode(), addr)


if __name__ == "__main__":
    main()
