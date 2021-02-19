import asyncio
import random
import time
import requests
import ory_hydra_client as hydra
import admin_client as ac
from authlib.integrations.requests_client import OAuth2Session
from authlib.common.security import generate_token


def initialise(admin_client, clients=1000, max_time=100):
    """
    Create clients for the test to run on
    :param admin_client:
    :param clients:
    :param max_time:
    :return:
    """
    oauth_clients = []

    client_intervals = []
    added_clients = 0
    while added_clients < clients:
        rc = random.randint(0, clients)
        if (rc + added_clients) > clients:
            rc = rc - ((added_clients + rc) - clients)

        added_clients += rc

        client_intervals.append(rc)

    client_sleeps = []
    added_sleeps = 0

    while added_sleeps < max_time:
        rc = random.randint(0, max_time)
        if (rc + added_sleeps) > max_time:
            rc = rc - ((added_sleeps + rc) - max_time)

        added_sleeps += rc
        client_sleeps.append(rc)

    print(f'Generated clients in groups: {client_intervals}')
    print(f'Generated client sleep intervals: {client_sleeps}')

    async def _call_gen():
        return admin_client.gen_client()

    async def _inner(oauth_clients):
        for i in client_intervals:
            tasks = []
            for y in range(0, i):
                tasks.append(asyncio.ensure_future(_call_gen()))

            t = await asyncio.gather(*tasks)
            oauth_clients += [x for x in t if x is not None]
            # time.sleep(5)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_inner(oauth_clients))
    loop.close()
    return oauth_clients


def initiate_login(clients, host='127.0.0.1', port=4444, scope='openid email'):
    # initialise authorization code grant type
    client = OAuth2Session(clients[0]['client_id'], clients[0]['client_secret'], scope=scope)
    nonce = generate_token()
    uri, state = client.create_authorization_url(f'http://{host}:{port}/oauth2/auth',
                                                 redirect_uri='http://127.0.0.1:3000/login')
    print(uri)
    # resp = requests.get(uri)
    # print('get redirect', resp)
    # token = client.fetch_token(f'http://{host}:{port}/oauth/access_token')
    # Initialise the login
    # resp = requests.get(uri)
    # print(resp)


def tester(args):
    config = {
        'clients': 1000,
        'clients_max_time': 100,
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

    if args.clients_max_time:
        config["clients_max_time"] = args.clients_max_time

    print('Running with configs:', config)

    admin_url = f'http://{config["host"]}:{config["admin_port"]}'
    public_url = f'http://{config["host"]}:{config["public_port"]}'

    admin_config = hydra.Configuration.get_default_copy()
    admin_config.host = admin_url
    admin_client = ac.AdminHydra(hydra.ApiClient(configuration=admin_config))

    public_config = hydra.Configuration.get_default_copy()
    public_config.host = public_url
    public_client = hydra.ApiClient(configuration=public_config)

    wait_time = 2
    max_time = 100
    oauth_clients = []

    while True:
        try:
            # we will try initialise clients here
            # since we are relying on external services, this could fail
            # so we wrap in a try-catch and wait
            print("Initialising clients...")
            oauth_clients = initialise(admin_client, clients=config["clients"],
                                       max_time=config["clients_max_time"])

            if len(oauth_clients) < config["clients"]:
                print(f'not all clients could be created! rerun and check that everything is okay with hydra')
            else:
                print(f'no. oauth clients created successfully: {len(oauth_clients)}')

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

    initiate_login(clients=oauth_clients, host=config['host'], port=config['public_port'])
