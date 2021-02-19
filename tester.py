import asyncio
import time

import ory_hydra_client as hydra
import admin_client as ac


def initialise(admin_client, public_client, clients=1000):
    oauth_clients = []

    for i in range(0, clients):
        oauth_clients.append(ac.gen_client(admin_client))

    # async def _call_gen():
    #     return ac.gen_client(admin_client=admin_client)
    #
    # async def _inner():
    #     tasks = []
    #     for i in clients:
    #         tasks.append(asyncio.create_task(_call_gen()))
    #
    #     oauth_clients = await asyncio.gather(*tasks)
    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(_inner())
    return oauth_clients


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
        config["run_for"] = args.run_for

    if args.clients:
        config["clients"] = args.clients

    if args.failure_rate:
        config["failure_rate"] = args.failure_rate

    if args.host:
        config["host"] = args.host

    if args.admin_port:
        config["admin_port"] = args.admin_port

    if args.public_port:
        config["public_port"] = args.public_port

    print('Running with configs:', config)

    admin_url = f'http://{config["host"]}:{config["admin_port"]}'
    public_url = f'http://{config["host"]}:{config["public_port"]}'

    admin_config = hydra.Configuration.get_default_copy()
    admin_config.host = admin_url
    admin_client = hydra.ApiClient(configuration=admin_config)

    public_config = hydra.Configuration.get_default_copy()
    public_config.host = public_url
    public_client = hydra.ApiClient(configuration=public_config)

    wait_time = 2
    max_time = 100
    while True:
        try:
            oauth_clients = initialise(admin_client, public_client, clients=config["clients"])
            print(f'no. oauth clients created successfully: {len(oauth_clients)}')
            print(f'clients: ', oauth_clients)

            break
        except Exception as e:
            print(e)
            pass
        wait_time *= 2
        if wait_time > max_time:
            print(
                f'Ending tester due to initialisation failure. Wait time has exceeded max_time: '
                f'({wait_time} > {max_time})')
            break
        time.sleep(wait_time)
