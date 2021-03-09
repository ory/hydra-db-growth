import json
import random
import sqlite3

import pandas as pd
from flask import Flask, request, render_template

app = Flask(__name__)
database = None


@app.route("/")
def hello():
    return render_template('index.html')


@app.route("/raw")
def raw():
    with sqlite3.connect('test.db') as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT * "
            "FROM DBGrowth ")

        data = cursor.fetchall()
    return json.dumps(data)


@app.route("/data")
def data():
    with sqlite3.connect('test.db') as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT (Services.SERVICE_NAME || '_' || Tables.TABLE_NAME) as SERVICE_TABLE, "
            "datetime(DBGrowth.TIME, 'unixepoch', 'localtime'), "
            "DBGrowth.SIZE "
            "FROM DBGrowth "
            "INNER JOIN Services ON Services.SERVICE_ID = DBGrowth.SERVICE_ID "
            "INNER JOIN Tables ON Tables.TABLE_ID = DBGrowth.TABLE_ID")

        data = cursor.fetchall()

        df = pd.DataFrame(data,
                          columns=['service_table', 'x', 'y'])

        unique_service_table = df.service_table.unique()

        datasets = pd.DataFrame(columns=['label', 'data', 'type'])

        for x in unique_service_table:
            vals = df.loc[df['service_table'] == x]
            del vals['service_table']
            number_of_colors = 1

            color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                     for i in range(number_of_colors)]

            datasets = datasets.append({'label': x, 'type': 'line', 'data': vals, 'borderColor': color[0]},
                                       ignore_index=True, sort=False)

    return datasets.to_json(orient='records')


@app.route("/error")
def error():
    return "You got an error."


@app.route("/login", methods=['GET'])
def login():
    return "You are getting the login screen"


@app.route("/consent", methods=['GET'])
def consent():
    return "You are getting the consent screen"


@app.route("/ping", methods=['GET'])
def ping():
    return {'status': 'ok'}


def server(args, db):
    configs = {
        'port': 3000,
        'host': '127.0.0.1'
        }

    if args.host:
        configs['host'] = args.host

    if args.port:
        configs['port'] = args.port

    global database
    database = db

    app.run(port=configs["port"], host=configs["host"], threaded=True)
