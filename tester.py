import time

import ory_hydra_client as hydra
import admin_client as ac


def initialise(admin_client, public_client):
    ac.gen_client(admin_client=admin_client)


def tester(args):
    config = {
        'clients': 1000,
        'failure_rate': 90,
        'run_for': 5,
        'host': '127.0.0.1',
        'admin_port': '4445',
        'public_port': '4444',
        }

    if args.run_for:
        config.run_for = args.run_for

    if args.clients:
        config.clients = args.clients

    if args.failure_rate:
        config.failure_rate = args.failure_rate

    if args.host:
        print('host')
        config.host = args.host

    if args.admin_port:
        config.admin_port = args.admin_port

    if args.public_port:
        config.public_port = args.public_port

    admin_url = f'http://{config["host"]}:{config["admin_port"]}'
    public_url = f'http://{config["host"]}:{config["public_port"]}'

    admin_config = hydra.Configuration.get_default_copy()
    admin_config.host = admin_url
    admin_client = hydra.ApiClient(configuration=admin_config)

    public_config = hydra.Configuration.get_default_copy()
    public_config.host = public_url
    public_client = hydra.ApiClient(configuration=public_config)

    wait_time = 1
    while True:
        try:
            initialise(admin_client, public_client)
        except:
            pass
        wait_time *= 2
        time.sleep(wait_time)
