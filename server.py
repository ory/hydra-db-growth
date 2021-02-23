import json
import logging
import sqlite3
from datetime import datetime
import pandas as pd

from flask import Flask, request, render_template, session

app = Flask(__name__)
database = None


@app.route("/")
def hello():
    return render_template('index.html')


@app.route("/data")
def raw():
    with sqlite3.connect('test.db') as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT (Services.SERVICE_NAME || '_' || Tables.TABLE_NAME) as SERVICE_TABLE, "
            "datetime(DBGrowth.TIME, 'unixepoch', 'localtime'), "
            "DBGrowth.SIZE "
            "FROM DBGrowth "
            "INNER JOIN Services ON Services.SERVICE_ID = DBGrowth.SERVICE_ID "
            "INNER JOIN Tables ON Tables.SERVICE_ID = Services.SERVICE_ID")

        data = cursor.fetchall()

        df = pd.DataFrame(data,
                          columns=['service_table', 'x', 'y'])

        unique_service_table = df.service_table.unique()

        datasets = pd.DataFrame(columns=['label', 'data', 'type'])

        for x in unique_service_table:
            vals = df.loc[df['service_table'] == x]
            del vals['service_table']
            datasets = datasets.append({'label': x, 'type': 'line', 'data': vals}, ignore_index=True, sort=False)

        # for x in df:
        #     df_by_table = df_by_table.append({'service_name': df['service_name'], x})

        # for x in data:
        #     cursor.execute(
        #         "SELECT TIME, CYCLE, REGISTERED_CLIENTS, SERVICE, ACTION, SIZE, SIZE_UNIT FROM DBGrowth "
        #         "WHERE TABLE_NAME = ?"
        #         "GROUP BY SERVICE "
        #         "ORDER BY TIME asc", (x[0],))
        #
        #     tables_data = cursor.fetchall()
        #     df = pd.DataFrame(tables_data,
        #                       columns=['time', 'cycle', 'registered_clients', 'service', 'action', 'size',
        #                                'size_unit'])
        #
        #     df_by_table = df_by_table.append({'y': x[0], 'x': df}, ignore_index=True, sort=False)

    return datasets.to_json(orient='records')

    data = cursor.fetchall()
    registered_clients = []
    transformed = []
    for x in data:
        date = datetime.utcfromtimestamp(int(x[0])).strftime('%Y-%m-%d %H:%M:%S')
        transformed.append({'x': date, 'y': x[7]})
        registered_clients.append({'cycle': x[1], 'clients': [2]})
    return json.dumps(data)


@app.route("/error")
def error():
    return "You got an error."


@app.route("/login", methods=['GET'])
def login():
    challenge = request.args.get('login_challenge')
    return "You are getting the login screen"


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

    app.run(port=configs["port"], host=configs["host"])
