#!/usr/bin/env python

from flask import Flask, request
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/sparql", methods = ["POST"])
def sparql():
    return request.form["payload"]


if __name__ == "__main__":
    app.run(port=8088, debug=True)