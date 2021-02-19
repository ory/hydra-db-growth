import argparse

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
    tester_parser.add_argument("--failure-rate", type=int,
                               help="Specify (in percentage) the failure rate")
    tester_parser.add_argument("--run-for", type=int,
                               help="Specify number of minutes the tester should run for (no. clients)/(no. "
                                    "minutes)= no.clients/pm")

    server_parser.add_argument('--host', type=str,
                               help='Specify the server binding address e.g. default: 127.0.0.1')
    server_parser.add_argument('--port', type=int,
                               help='Specify the server binding port e.g. default: 3000')

    return parser.parse_args()


def main(args):
    args.func(args)


if __name__ == "__main__":
    main(args_parser())
