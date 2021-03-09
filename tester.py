import concurrent.futures
import logging
import os
import random
import time
import uuid
from datetime import datetime
from math import floor
from urllib.parse import urlparse, parse_qs

import requests
from authlib.integrations.requests_client import OAuth2Session

from database.database import DatabaseController
from database.mysql import MysqlController
from database.postgresql import PostgresqlController

test_logger = logging.getLogger('tester')


def save_result_to_sqlite(db,
                          action,
                          data={'cycle': 0, 'registered_clients': 0, 'service': 'hydra', 'size_unit': 'MB', 'results': []}):
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO Services (SERVICE_NAME) VALUES (?)", (data['service'],))
        db.commit()
    except:
        pass

    cursor.execute("SELECT SERVICE_ID FROM Services WHERE SERVICE_NAME = ?", (data['service'],))
    service_id = cursor.fetchone()[0]

    for x in data['results']:
        try:
            cursor.execute("INSERT INTO Tables (TABLE_NAME, SERVICE_ID) "
                           "VALUES(?, ?)",
                           (f'{data["service"]}_{x[0]}', service_id))
            db.commit()
        except:
            pass

        cursor.execute("SELECT TABLE_ID FROM Tables WHERE TABLE_NAME = ? AND SERVICE_ID = ?",
                       (f'{data["service"]}_{x[0]}', service_id,))
        table_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO DBGrowth (TIME, CYCLE, REGISTERED_CLIENTS, ACTION, SIZE, SIZE_UNIT, SERVICE_ID, TABLE_ID) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (int(time.time()), data['cycle'], data['registered_clients'], action,
             (int(x[1]) / 1024 / 1024), data['size_unit'],
             service_id, table_id,))

        db.commit()


def initialise(config, url, clients=1000, max_time=100):
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

    test_logger.info(f'Generated clients in groups: {client_intervals}')
    test_logger.info(f'Generated client sleep intervals: {client_sleeps}')

    def _call_gen():
        client_id = str(uuid.uuid4())
        client_secret = str(uuid.uuid4())

        resp = requests.post(f'{url}/clients', json={'client_id': client_id,
                                                     'grant_types': ['authorization_code', 'refresh_token'],
                                                     'scope': 'openid offline',
                                                     'response_types': ['code'],
                                                     'redirect_uris': [
                                                         f'http://{config["flask_host"]}:{config["flask_port"]}/login',
                                                         f'http://{config["flask_host"]}:{config["flask_port"]}/consent']})
        if resp.status_code == 201:
            return {'client_id': client_id, 'client_secret': client_secret}
        else:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for i in client_intervals:
            for y in range(0, i):
                futures.append(executor.submit(_call_gen))

        for future in concurrent.futures.as_completed(futures):
            try:
                oauth_clients.append(future.result())
            except Exception as e:
                test_logger.error(e)
                pass

    return oauth_clients


def accept_login(client, host, port):
    resp = client['session'].put(
        f'http://{host}:{port}/oauth2/auth/requests/login/accept?login_challenge={client["login_challenge"]}',
        json={'subject': client['client_id']})
    if resp.ok:
        resp2 = client['session'].get(resp.json()['redirect_to'])
        client['consent_challenge'] = parse_qs(urlparse(resp2.url).query)['consent_challenge'][0]
        return client

    return None


def accept_consent(client, host, port):
    resp = client['session'].put(
        f'http://{host}:{port}/oauth2/auth/requests/consent/accept?consent_challenge={client["consent_challenge"]}',
        json={})
    if resp.ok:
        resp2 = client['session'].get(resp.json()['redirect_to'])
        if resp2.ok:
            return True

    return None


def reject_login(client, host, port):
    resp = client['session'].put(
        f'http://{host}:{port}/oauth2/auth/requests/login/reject?login_challenge={client["login_challenge"]}',
        json={})
    return resp.ok


def reject_consent(client, host, port):
    resp = client['session'].put(
        f'http://{host}:{port}/oauth2/auth/requests/consent/reject?consent_challenge={client["consent_challenge"]}',
        json={})
    resp2 = client['session'].get(resp.json()['redirect_to'])
    return resp2.ok


def flush(session, host, port):
    test_logger.info("Running Flush...")
    resp = session.post(f'http://{host}:{port}/oauth2/flush', json={})
    return resp.ok


def initiate_clients_consent(clients, host='127.0.0.1', port=4445):
    def _consent(client):
        resp = client['session'].get(
            f'http://{host}:{port}/oauth2/auth/requests/consent?consent_challenge={client["login_challenge"]}',
            allow_redirects=False)
        if resp.ok:
            return client
        return None

    consent_clients = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = (executor.submit(_consent, c) for c in clients)

        for futures in concurrent.futures.as_completed(futures):
            try:
                consent_clients.append(futures.result())
            except Exception as e:
                test_logger.error(e)
                pass
        return [x for x in consent_clients if x is not None]


def initiate_clients_login(clients, host='127.0.0.1', port=4444, scope='openid offline',
                           redirect='http://127.0.0.1:3000/login'):
    def _login(client):
        session = requests.Session()
        c = OAuth2Session(client_id=client['client_id'], client_secret=client['client_secret'],
                          scope=scope)
        uri, state = c.create_authorization_url(f'http://{host}:{port}/oauth2/auth',
                                                redirect_uri=redirect)

        resp = session.get(uri, allow_redirects=False)

        if resp.ok:
            client['login_challenge'] = parse_qs(urlparse(resp.headers.get('location')).query)['login_challenge'][0]
            client['session'] = session
            return client
        else:
            test_logger.error('Login redirect failed for client_id: ', clients[0]['client_id'])
            return None

    logged_in_clients = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = (executor.submit(_login, c) for c in clients)
        for future in concurrent.futures.as_completed(futures):
            try:
                logged_in_clients.append(future.result())
            except Exception as e:
                test_logger.error(e)
                pass

    return logged_in_clients


def _tester(cycle, config, db, external_db, working_data):
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
            test_logger.info("Initialising clients...")
            oauth_clients = initialise(config, admin_url, clients=config["clients"],
                                       max_time=config["clients_max_time"])

            working_data['results'] = db_sizes = external_db.gen_hydra_report()
            test_logger.info(f'SIZE {working_data["results"]}')
            save_result_to_sqlite(db, 'clients_created', working_data)
            test_logger.info(f'Cycle: {cycle} | Action: Clients Created | {datetime.now()} | db_size: {db_sizes}')

            if len(oauth_clients) < config["clients"]:
                test_logger.error(
                    'not all clients could be created! rerun and check that everything is okay with hydra')
            else:
                test_logger.debug(f'no. oauth clients created successfully: {len(oauth_clients)}')
            break
        except Exception as e:
            test_logger.error(e)
            pass
        wait_time *= 2
        if wait_time > max_time:
            test_logger.error(
                f'Ending tester due to initialisation failure. Wait time has exceeded max_time: '
                f'({wait_time} > {max_time})')
            break
        test_logger.info('retrying...')
        time.sleep(wait_time)

    oauth_clients = initiate_clients_login(clients=oauth_clients, host=config['host'],
                                           port=config['public_port'],
                                           redirect=f'http://{config["flask_host"]}:{config["flask_port"]}/login')

    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'client_login_init', working_data)
    test_logger.info(f'Cycle: {cycle} | Action: After client login init  | {datetime.now()} | db_size: {db_sizes}')

    oauth_clients = [x for x in oauth_clients if 'login_challenge' in x]
    c = floor(len(oauth_clients) * (config['login_failure_rate'] / 100))
    clients_reject = oauth_clients[0:c]
    clients_accept = oauth_clients[len(clients_reject):len(oauth_clients)]
    clients_timeout = clients_reject[0:floor(len(clients_reject) * (config['timeout_reject_ratio'] / 100))]
    # clients rejecting the auth would probably be less than those timing out (or never completing the request)
    clients_reject = clients_reject[len(clients_timeout):len(clients_reject)]

    client_accept_tasks = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = (executor.submit(accept_login,
                                   client=c,
                                   host=config['host'],
                                   port=config['admin_port']) for c in clients_accept)

        for future in concurrent.futures.as_completed(futures):
            try:
                client_accept_tasks.append(future.result())
            except Exception as e:
                test_logger.error(e)
                pass

        clients_accept = [x for x in client_accept_tasks if x is not None]

    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'after_client_login_accept', working_data)
    test_logger.info(
        f'Cycle: {cycle} | Action: After client login accept  | {datetime.now()} | db_size: {db_sizes}')

    _ = initiate_clients_consent(clients=clients_accept, host=config['host'],
                                 port=config['admin_port'])

    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'after_client_consent_init', working_data)
    test_logger.info(
        f'Cycle: {cycle} | Action: After client consent init  | {datetime.now()} | db_size: {db_sizes}')

    c = floor(len(clients_accept) * (config['consent_failure_rate'] / 100))
    clients_reject_consent = clients_accept[0:c]
    clients_accept_consent = clients_accept[len(clients_reject_consent):len(clients_accept)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = (executor.submit(reject_consent,
                                   client=c,
                                   host=config['host'],
                                   port=config['admin_port']) for c in clients_reject_consent)

        for future in concurrent.futures.as_completed(futures):
            try:
                _ = future.result()
            except Exception as e:
                test_logger.error(e)
                pass

    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'after_client_consent_reject', working_data)
    test_logger.info(
        f'Cycle: {cycle} | Action: After client consent reject  | {datetime.now()} | db_size: {db_sizes}')

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = (executor.submit(accept_consent,
                                   client=c,
                                   host=config['host'],
                                   port=config['admin_port']) for c in clients_accept_consent)

        for future in concurrent.futures.as_completed(futures):
            try:
                _ = future.result()
            except Exception as e:
                test_logger.error(e)
                pass

    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'after_client_consent_accept', working_data)
    test_logger.info(
        f'Cycle: {cycle} | Action: After client consent accept  | {datetime.now()} | db_size: {db_sizes}')

    client_reject_tasks = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = (executor.submit(reject_login,
                                   client=c,
                                   host=config['host'],
                                   port=config['admin_port']) for c in clients_reject)

        for future in concurrent.futures.as_completed(futures):
            try:
                client_reject_tasks.append(future.result())
            except Exception as e:
                test_logger.error(e)
                pass

    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'after_client_login_reject', working_data)
    test_logger.info(
        f'Cycle: {cycle} | Action: After client login reject  | {datetime.now()} | db_size: {db_sizes}')

    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'before_client_timeout', working_data)
    test_logger.info(f'Cycle: {cycle} | Action: Before client timeout  | {datetime.now()} | db_size: {db_sizes}')

    test_logger.info(f'waiting for {config["ttl_timeout"]}s timeout of {len(clients_timeout)} clients')
    time.sleep(config["ttl_timeout"])
    working_data['results'] = db_sizes = external_db.gen_hydra_report()
    save_result_to_sqlite(db, 'after_client_timeout', working_data)
    test_logger.info(f'Cycle: {cycle} | Action: After client timeout  | {datetime.now()} | db_size: {db_sizes}')


def tester(args, db):
    config = {
        'flask_host': '127.0.0.1',
        'flask_port': 3000,
        'run_flush': False,
        'service_name': 'hydra',
        'clients': 1000,
        'clients_max_time': 100,
        'login_failure_rate': 90,
        'consent_failure_rate': 90,
        'timeout_reject_ratio': 90,
        'ttl_timeout': 60,
        'run_for': 5,
        'num_cycles': 5,
        'host': '127.0.0.1',
        'admin_port': '4445',
        'public_port': '4444',
        'db': {},
        }

    postgresql_configs = {
        'host': '127.0.0.1',
        'port': 5432,
        'username': 'postgres',
        'password': '',
        'name': 'hydra',
        }

    mysql_configs = {
        'host': '127.0.0.1',
        'port': 3306,
        'username': 'root',
        'password': '',
        'name': 'hydra',
        }

    if args.flask_host:
        config['flask_host'] = args.flask_host

    if args.flask_port:
        config['flask_port'] = args.flask_port

    if args.service_name:
        config['service_name'] = args.service_name

    if args.database == 'postgresql':
        config['db'] = postgresql_configs
    else:
        config['db'] = mysql_configs

    if args.db_host:
        config['db']['host'] = args.db_host

    if args.db_port:
        config['db']['port'] = args.db_port

    if args.db_username:
        config['db']['username'] = args.db_username

    if args.db_password:
        config['db']['password'] = args.db_password

    if args.db_name:
        config['db']['name'] = args.db_name

    if args.run_for:
        config["run_for"] = args.run_for

    if args.num_cycles:
        config["num_cycles"] = args.num_cycles

    if args.clients:
        config["clients"] = args.clients

    if args.login_failure_rate:
        config["login_failure_rate"] = args.login_failure_rate

    if args.consent_failure_rate:
        config["consent_failure_rate"] = args.consent_failure_rate

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

    if args.run_flush:
        config["run_flush"] = args.run_flush

    test_logger.info(f'Running with configs: {config}')

    if args.database == 'postgresql':
        external_db = DatabaseController(PostgresqlController(connection=config['db']))
    else:
        external_db = DatabaseController(MysqlController(connection=config['db']))

    logging.info(f'db connection established {external_db is not None}')

    if config["run_flush"]:
        if os.path.isdir('.build'):
            os.system("cd .build/hydra; git checkout db-growth; git pull; go build -tags sqlite -o hydra")
        else:
            os.system("./scripts/build_hydra.sh")

    working_data = {
        'cycle': 0,
        'registered_clients': 0,
        'service': config['service_name'],
        'size_unit': 'MB',
        'results': []
        }

    while True:
        resp = requests.get(f'http://{config["flask_host"]}:{config["flask_port"]}/ping')
        if resp.ok:
            break
        time.sleep(2)

    for c in range(0, config["num_cycles"]):
        working_data['cycle'] = c
        working_data['registered_clients'] = external_db.get_registered_clients()
        test_logger.info(f'registered clients {working_data["registered_clients"]}')
        _tester(c, config, db, external_db, working_data)

        if config['run_flush']:
            if args.database == 'postgresql':
                db_driver = "postgres"
            else:
                db_driver = "mysql"

            os.environ[
                'DSN'] = f'{db_driver}://{config["db"]["username"]}:{config["db"]["password"]}@{config["db"]["host"]}:{config["db"]["port"]}/{config["db"]["name"]}?sslmode=disable&max_conns=20&max_idle_conns=4'

            ok = os.system(".build/hydra/hydra janitor -e")
            test_logger.info(ok)

            working_data['results'] = db_sizes = external_db.gen_hydra_report()
            save_result_to_sqlite(db, 'After flush', working_data)
            test_logger.info(f'Cycle: {c} | Action: After flush  | {datetime.now()} | db_size: {db_sizes}')
