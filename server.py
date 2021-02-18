from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/login")
def login():
    return True


def server(args):
    configs = {
        'port': 3000,
        'host': '127.0.0.1'
        }

    if args.host:
        configs.host = args.host

    if args.port:
        configs.port = args.port

    app.run(port=configs["port"], host=configs["host"])
