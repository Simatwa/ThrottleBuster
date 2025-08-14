from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/headers")
def main():
    resp = dict(request.headers)
    print(resp)
    return jsonify(resp)


@app.route("/cookies")
def main_1():
    resp = dict(request.cookies)
    print(resp)
    return jsonify(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
