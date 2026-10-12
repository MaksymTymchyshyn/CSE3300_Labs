"""Fibonacci Server (FS).

PUT /register            -> registers its hostname with the AS over UDP, returns 201
GET /fibonacci?number=X  -> returns the X-th Fibonacci number (200) or 400 if X is bad
"""
import socket

from flask import Flask, jsonify, request

app = Flask(__name__)

TTL = 10


def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


@app.route("/register", methods=["PUT"])
def register():
    body = request.get_json(silent=True)
    if not body:
        return jsonify(error="Body must be a JSON object"), 400

    hostname = body.get("hostname")
    ip = body.get("ip")
    as_ip = body.get("as_ip")
    as_port = body.get("as_port")
    if not all([hostname, ip, as_ip, as_port]):
        return jsonify(error="hostname, ip, as_ip and as_port are required"), 400
    try:
        as_port = int(as_port)
    except (TypeError, ValueError):
        return jsonify(error="as_port must be an integer"), 400

    message = f"TYPE=A\nNAME={hostname} VALUE={ip} TTL={TTL}\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.sendto(message.encode(), (as_ip, as_port))
        reply, _ = sock.recvfrom(2048)
    except OSError as e:
        return jsonify(error=f"Could not reach authoritative server: {e}"), 500
    finally:
        sock.close()

    reply = reply.decode()
    if f"VALUE={ip}" not in reply:
        return jsonify(error="Registration failed", as_response=reply), 500

    return jsonify(message="Registered", hostname=hostname, ip=ip), 201


@app.route("/fibonacci", methods=["GET"])
def get_fibonacci():
    number = request.args.get("number")
    try:
        n = int(number)
    except (TypeError, ValueError):
        return jsonify(error="number must be an integer"), 400
    if n < 0:
        return jsonify(error="number must be non-negative"), 400
    return jsonify(number=n, fibonacci=fibonacci(n)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
