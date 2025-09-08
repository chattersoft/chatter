from flask import Flask, request, send_file
import hashlib
import json
import os

app = Flask(__name__)

USER_FILE = "users.txt"
SALT_FILE = "salt.txt"
MSG_FILE = "messages.txt"

def sha256_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def calculate_salt(birthday: str) -> str:
    digits = [int(ch) for ch in birthday if ch.isdigit()]
    return str(sum(digits))

@app.route("/", methods=["GET"])
@app.route("/home.html", methods=["GET"])
def serve_home():
    return send_file("home.html", mimetype="text/html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    birthday = data.get("birthday", "").strip()

    if not username or not password or not birthday:
        return "Missing fields", 400

    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            for line in f:
                if line.split(":")[0] == username:
                    return "User already registered", 400

    salt = calculate_salt(birthday)
    hashed = sha256_hash(password + salt)

    with open(USER_FILE, "a") as f:
        f.write(f"{username}:{hashed}\n")

    with open(SALT_FILE, "a") as f:
        f.write(f"{username}:{salt}\n")

    return "User registered"

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return "Missing fields", 400

    user_hash = None
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if parts[0] == username:
                    user_hash = parts[1]
                    break

    if not user_hash:
        return "User not found", 404

    salt = None
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if parts[0] == username:
                    salt = parts[1]
                    break

    if not salt:
        return "Salt not found", 500

    check_hash = sha256_hash(password + salt)
    if check_hash == user_hash:
        return "Login successful"
    else:
        return "Invalid password", 403

@app.route("/message", methods=["GET", "POST"])
def message():
    if request.method == "GET":
        try:
            with open(MSG_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "No messages found", 404
    else:
        msg = request.data.decode("utf-8").strip()
        with open(MSG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        return "Message sent"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)