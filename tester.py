import asyncio
import random
import time
import uuid
from math import floor
from urllib.parse import urlparse, parse_qs

import requests
from authlib.integrations.requests_client import OAuth2Session


def initialise(url, clients=1000, max_time=100):
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
        client_id = str(uuid.uuid4())
        client_secret = str(uuid.uuid4())

        resp = requests.post(f'{url}/clients', json={'client_id': client_id,
                                                     'grant_types': ['authorization_code', 'refresh_token'],
                                                     'scope': 'openid offline',
                                                     'response_types': ['code'],
                                                     'redirect_uris': ['http://127.0.0.1:3000/login']})
        if resp.status_code == 201:
            return {'client_id': client_id, 'client_secret': client_secret}
        else:
            return None

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
    return oauth_clients


def accept_login(host, port, login_challenge, client_id):
    resp = requests.put(f'http://{host}:{port}/oauth2/auth/requests/login/accept?login_challenge={login_challenge}',
                        json={'subject': client_id})
    return resp.ok


def reject_login(host, port, login_challenge):
    resp = requests.put(f'http://{host}:{port}/oauth2/auth/requests/login/reject?login_challenge={login_challenge}',
                        json={})
    print(resp.text)
    return resp.ok


def login_details(url):
    resp = requests.get(url)
    print('login details', resp.text)


def initiate_clients_login(clients, host='127.0.0.1', port=4444, scope='openid offline'):
    for i in range(0, len(clients)):
        # initialise authorization code grant type
        client = OAuth2Session(client_id=clients[0]['client_id'], client_secret=clients[0]['client_secret'],
                               scope=scope)
        uri, state = client.create_authorization_url(f'http://{host}:{port}/oauth2/auth',
                                                     redirect_uri='http://127.0.0.1:3000/login')
        print(uri)
        resp = requests.get(uri)
        if resp.ok:
            print('Attempt OAuth login: ', resp.ok, resp.text, '\n', resp.url)
            login_challenge = parse_qs(urlparse(resp.url).query)['login_challenge'][0]
            print('login_challenge: ', login_challenge)
            clients[i]['login_challenge'] = login_challenge
        else:
            print('Login redirect failed for client_id: ', clients[0]['client_id'])
    return clients


def _tester(config):
    admin_url = f'http://{config["host"]}:{config["admin_port"]}'
    public_url = f'http://{config["host"]}:{config["public_port"]}'

    wait_time = 2
    max_time = 100
    oauth_clients = []

    while True:
        try:
            # we will try initialise clients here
            # since we are relying on external services, this could fail
            # so we wrap in a try-catch and wait
            print("Initialising clients...")
            oauth_clients = initialise(admin_url, clients=config["clients"],
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

    oauth_clients = initiate_clients_login(clients=oauth_clients, host=config['host'], port=config['public_port'])

    oauth_clients = [x for x in oauth_clients if 'login_challenge' in x]
    c = floor(len(oauth_clients) * (config['failure_rate'] / 100))
    clients_reject = oauth_clients[0:c]
    clients_accept = oauth_clients[len(clients_reject):len(oauth_clients)]
    clients_timeout = clients_reject[0:floor(len(clients_reject) * (config['timeout_reject_ratio'] / 100))]
    # clients rejecting the auth would probably be less than those timing out (or never completing the request)
    clients_reject = clients_reject[len(clients_timeout):len(clients_reject)]

    for ca in clients_accept:
        ok = accept_login(host=config['host'], port=config['admin_port'],
                          login_challenge=ca["login_challenge"],
                          client_id=ca["client_id"])

        print('accept_login', ok)

    for cr in clients_reject:
        ok = reject_login(host=config['host'], port=config['admin_port'],
                          login_challenge=cr["login_challenge"])
        print('reject_login', ok)

    print('waiting for timeout for these clients:', clients_timeout)
    time.sleep(config["ttl_timeout"])


def tester(args):
    config = {
        'clients': 1000,
        'clients_max_time': 100,
        'failure_rate': 90,
        'timeout_reject_ratio': 90,
        'ttl_timeout': 60,
        'run_for': 5,
        'num_cycles': 5,
        'host': '127.0.0.1',
        'admin_port': '4445',
        'public_port': '4444',
        }

    if args.run_for:
        config["run_for"] = args.run_for

    if args.num_cycles:
        config["num_cycles"] = args.num_cycles

    if args.clients:
        config["clients"] = args.clients

    if args.failure_rate:
        config["failure_rate"] = args.failure_rate

    if args.timeout_reject_ratio:
        config["timeout_reject_ratio"] = args.timeout_reject_ratio

    if args.ttl_timeout:
        config["ttl_timeout"] = args.ttl_timeout

    if args.host:
        config["host"] = args.host

    if args.admin_port:
        config["admin_port"] = args.admin_port

    if args.public_port:
        config["public_port"] = args.public_port

    if args.clients_max_time:
        config["clients_max_time"] = args.clients_max_time

    print('Running with configs:', config)

    for c in range(0, config["num_cycles"]):
        _tester(config)
