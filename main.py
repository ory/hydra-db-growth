import argparse
import logging
import sqlite3
from tester import tester
from server import server


def args_parser():
    parser = argparse.ArgumentParser(prog='Hydra Database growth tester')

    subparsers = parser.add_subparsers(help='sub-command help')

    tester_parser = subparsers.add_parser('tester', help='Start the testing programme')
    tester_parser.set_defaults(func=tester)

    server_parser = subparsers.add_parser('server', help='Start the web server for reporting and stats')
    server_parser.set_defaults(func=server)

    tester_parser.add_argument("--host", type=str, help="Specify the server host")

    tester_parser.add_argument("--admin-port", type=int, help="Specify the server admin port")

    tester_parser.add_argument("--public-port", type=int,
                               help="Specify the server public port")

    tester_parser.add_argument("--clients", type=int, help="Specify number of clients")

    tester_parser.add_argument("--clients-max-time", type=int, help="Max time assigned to client creation (in seconds)")

    tester_parser.add_argument("--login-failure-rate", type=int,
                               help="Specify (in percentage) the login failure rate")

    tester_parser.add_argument("--consent-failure-rate", type=int,
                               help="Specify (in percentage) the consent failure rate")

    tester_parser.add_argument("--timeout-reject-ratio", type=int,
                               help="Specify (in percentage) the timeout rate of a client appose to a client rejecting")
    tester_parser.add_argument("--run-for", type=int,
                               help="Specify number of minutes the tester should run for (no. clients)/(no. "
                                    "minutes)= no.clients/pm")
    tester_parser.add_argument("--num-cycles", type=int,
                               help="Specify the number of cycles the tester should run for.")

    tester_parser.add_argument("--ttl-timeout", type=int,
                               help="Specify the ttl timeout in seconds.")

    tester_parser.add_argument("--database", type=str,
                               help="The database which should be queried, e.g. postgresql or mysql")

    tester_parser.add_argument("--db-host", type=str, help="The database ip")

    tester_parser.add_argument("--db-port", type=int, help="The database port")

    tester_parser.add_argument("--db-username", type=str, help="The database username")

    tester_parser.add_argument("--db-password", type=str, help="The database password")

    tester_parser.add_argument("--db-name", type=str, help="The database name e.g. hydra")

    tester_parser.add_argument("--service-name", type=str, help="The service being tested (will be saved in sqlite db)")

    tester_parser.add_argument("--run-flush", action='store_true', help="Run the flush command after each cycle")

    tester_parser.add_argument("--flask-host", type=str, help="Specify the flask server host e.g. default: 127.0.0.1")

    tester_parser.add_argument("--flask-port", type=int,
                               help="Specify the flask server binding port e.g. default: 3000")

    server_parser.add_argument('--host', type=str,
                               help='Specify the server binding address e.g. default: 127.0.0.1')
    server_parser.add_argument('--port', type=int,
                               help='Specify the server binding port e.g. default: 3000')

    return parser.parse_args()


def init_db():
    """ create a database connection to a SQLite database """
    conn = sqlite3.connect('test.db')
    conn.execute("CREATE TABLE if not exists Services"
                 "(SERVICE_ID INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "SERVICE_NAME  CHAR(50) NOT NULL UNIQUE);")

    conn.execute("CREATE TABLE if not exists Tables"
                 "(TABLE_ID INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "TABLE_NAME    CHAR(50) UNIQUE,"
                 "SERVICE_ID    INTEGER     NOT NULL,"
                 "FOREIGN KEY (SERVICE_ID)"
                 "  REFERENCES Services (SERVICE_ID)"
                 ");")

    conn.execute("CREATE TABLE if not exists DBGrowth"
                 "(TIME                 INTEGER     NOT NULL, "
                 "CYCLE                 INTEGER     NOT NULL, "
                 "REGISTERED_CLIENTS    INTEGER     NOT NULL, "
                 "ACTION                CHAR(50)    NOT NULL,"
                 "SIZE                  INTEGER     NOT NULL,"
                 "SIZE_UNIT             CHAR(50)    NOT NULL,"
                 "TABLE_ID              INTEGER     NOT NULL, "
                 "SERVICE_ID            INTEGER     NOT NULL,"
                 "FOREIGN KEY (SERVICE_ID)"
                 "  REFERENCES Services (SERVICE_ID),"
                 "FOREIGN KEY (TABLE_ID)"
                 "  REFERENCES Tables (TABLE_ID));")

    conn.commit()
    logging.info('Opened sqlite db successfully')
    return conn


def main(args):
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    db = init_db()
    args.func(args, db)


if __name__ == "__main__":
    main(args_parser())
