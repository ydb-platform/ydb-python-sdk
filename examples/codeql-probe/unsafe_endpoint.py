"""Intentionally vulnerable CodeQL probe. Do not run or merge this example."""

from flask import Flask, request

app = Flask(__name__)


@app.route("/evaluate")
def evaluate_expression():
    expression = request.args["expression"]
    return str(eval(expression))
