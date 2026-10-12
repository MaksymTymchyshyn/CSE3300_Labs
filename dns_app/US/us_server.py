"""User Server (US).

GET /fibonacci?hostname=fibonacci.com&fs_port=K&number=X&as_ip=Y&as_port=Z

1. Asks the Authoritative Server (UDP) for the IP address of `hostname`.
2. Requests http://<ip>:<fs_port>/fibonacci?number=X from the Fibonacci Server.
3. Returns the Fibonacci number with 200, or 400 if any parameter is missing.
"""
import socket

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

REQUIRED = ["hostname", "fs_port", "number", "as_ip", "as_port"]


def dns_query(hostname, as_ip, as_port):
    """Query the AS for an A record; return the IP address or None."""
    message = f"TYPE=A\nNAME={hostname}\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.sendto(message.encode(), (as_ip, as_port))
        reply, _ = sock.recvfrom(2048)
    finally:
        sock.close()

    fields = {}
    for token in reply.decode().split():
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key.upper()] = value
    return fields.get("VALUE")


@app.route("/fibonacci", methods=["GET"])
def fibonacci():
    params = {name: request.args.get(name) for name in REQUIRED}
    missing = [name for name, value in params.items() if not value]
    if missing:
        return jsonify(error=f"Missing parameters: {', '.join(missing)}"), 400

    try:
        as_port = int(params["as_port"])
        fs_port = int(params["fs_port"])
    except ValueError:
        return jsonify(error="as_port and fs_port must be integers"), 400

    try:
        fs_ip = dns_query(params["hostname"], params["as_ip"], as_port)
    except OSError as e:
        return jsonify(error=f"Could not reach authoritative server: {e}"), 500
    if not fs_ip:
        return jsonify(error=f"Hostname {params['hostname']} not found"), 404

    try:
        resp = requests.get(
            f"http://{fs_ip}:{fs_port}/fibonacci",
            params={"number": params["number"]},
            timeout=5,
        )
    except requests.RequestException as e:
        return jsonify(error=f"Could not reach Fibonacci server: {e}"), 500

    # Pass the FS answer (200, or 400 for a non-integer number) straight through
    return resp.content, resp.status_code, {"Content-Type": resp.headers.get("Content-Type", "application/json")}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
