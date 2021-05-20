import logging
import uuid

import requests
from authlib.integrations.requests_client import OAuth2Session
from urllib.parse import urlparse, parse_qs

hydra_logger = logging.getLogger('hydra')


def init_login(client, host, port, scope='openid offline', redirect='http://127.0.0.1:3000/login'):
    client['session'] = requests.Session()
    c = OAuth2Session(client_id=client['client_id'], client_secret=client['client_secret'],
                      scope=scope)
    uri, state = c.create_authorization_url(f'http://{host}:{port}/oauth2/auth',
                                            redirect_uri=redirect)

    resp = client['session'].get(uri, allow_redirects=False)

    if resp.ok:
        client['login_challenge'] = parse_qs(urlparse(resp.headers.get('location')).query)['login_challenge'][0]
        return client
    else:
        hydra_logger.error('Login redirect failed for client_id: ', client['client_id'])
        return None


def init_consent(client, host, port):
    resp = client['session'].get(
        f'http://{host}:{port}/oauth2/auth/requests/consent?consent_challenge={client["login_challenge"]}',
        allow_redirects=False)
    if resp.ok:
        return client
    return None


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
    hydra_logger.info("Running Flush...")
    resp = session.post(f'http://{host}:{port}/oauth2/flush', json={})
    return resp.ok


def create_client(config, host, port):
    url = f'http://{host}:{port}/clients'

    client_id = str(uuid.uuid4())
    client_secret = str(uuid.uuid4())

    resp = requests.post(url, json={'client_id': client_id,
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


def health(host, port):
    hydra_logger.info("Checking service health...")
    resp = requests.get(f'http://{host}:{port}/health/ready')

    if resp.status_code == 200:
        return True
    else:
        return False
