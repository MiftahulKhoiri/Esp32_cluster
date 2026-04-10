from flask import Flask, send_file, jsonify

app = Flask(__name__)

FIRMWARE_VERSION = "1.1"


@app.route("/firmware")

def firmware():

    return send_file("main.py")


@app.route("/version")

def version():

    return jsonify({

        "version": FIRMWARE_VERSION

    })


app.run(
    host="0.0.0.0",
    port=8000
)