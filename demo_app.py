import os

from flask import Flask, jsonify, request

APP = Flask(__name__)

PRODUCTS = {
    1: {"name": "Laptop", "price": 72000},
    2: {"name": "Keyboard", "price": 1800},
    3: {"name": "Mouse", "price": 750},
}


@APP.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "demo-app"})


@APP.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "message": "Demo app behind WAF",
            "routes": ["/search?q=term", "/login", "/product/1"],
        }
    )


@APP.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    return jsonify({"query": query, "result_count": 1, "results": [f"match:{query}"]})


@APP.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    return jsonify({"message": f"Welcome {username}", "authenticated": bool(username)})


@APP.route("/product/<int:product_id>", methods=["GET"])
def product(product_id: int):
    item = PRODUCTS.get(product_id)
    if item is None:
        return jsonify({"error": "product not found"}), 404
    return jsonify(item)


if __name__ == "__main__":
    APP.run(host=os.getenv("DEMO_HOST", "0.0.0.0"), port=int(os.getenv("DEMO_PORT", "5001")))
