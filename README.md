<h1 align="center">Hydra DB Growth</h1>

A way to test the growth of a db (mysql, postgresql, ...) when running Hydra. This is specifically related to this
issue: https://github.com/ory/hydra/issues/1574.

### Milestones

- [X] Graphs (time-series plot) of database size and other meta info
- [X] Easy Failure rate adjustment via cli
- [ ] Maybe extend the software to allow more tests of the different use cases of Hydra in respects to the database (
  currently login/consent requests are observed)

### What seems to be the issue

Users aren't finishing the Login flow - causing tables `hydra_oauth2_authentication_request`
and `hydra_oauth2_authentication_session` to explode in size.

### What is failure rate?

There are two failure rates:

- login-failure-rate
- consent-failure-rate

Failure rate is the rate at which clients do not complete the login/consent flow - this could be in timing out or simply
rejecting the flow.

According to https://github.com/ory/hydra/issues/1574#issuecomment-771573626 it seems out of 4000 login requests only
100 complete.

This only has an effect on the size of tables with the suffix `_handled` since no login/consent is completing, these
tables stay relatively small.

On the `_authentication_request` table this seems to have a very small effect in its growth.

### Running the test

```shell
./scripts/build.sh
./scripts/test.sh
```

Then there should be a UI running on http://127.0.0.1:3000.

The default tests run the following configurations

```shell
tester --host=hydra-postgresql --admin-port=6445 --public-port=6444 --clients=2 --login-failure-rate=90 --consent-failure-rate=90 --database=postgresql --db-host=postgresd --db-username=hydra --db-password=secret --db-name=hydra --service-name=hydra-postgresql --flask-host=hydra-growth-server --flask-port=3000
```

And:

```shell
tester --host=hydra-mysql --admin-port=5445 --public-port=5444 --clients=100 --login-failure-rate=90 --consent-failure-rate=90 --database=mysql --db-host=mysqld --db-username=root --db-password=secret --db-name=mysql --service-name=hydra-mysql --flask-host=hydra-growth-server --flask-port=3000
```

### Cleanup

**Cleanup also deletes the sqlite `test.db` which stores the results of the test**

    ./scripts/cleanup.sh

### Configurations

Default configs set in the programme:

```python

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
```

Run `python3 main.py -h`

    usage: Hydra Database growth tester [-h] {tester,server} ...
    
    positional arguments:
      {tester,server}  sub-command help
        tester         Start the testing programme
        server         Start the web server for reporting and stats
    
    optional arguments:
      -h, --help       show this help message and exit

#### Tester configs

Run `python3 main.py tester -h`

```shell
    usage: Hydra Database growth tester tester [-h] [--host HOST] [--admin-port ADMIN_PORT] [--public-port PUBLIC_PORT] [--clients CLIENTS] [--clients-max-time CLIENTS_MAX_TIME]
                                           [--login-failure-rate LOGIN_FAILURE_RATE] [--consent-failure-rate CONSENT_FAILURE_RATE] [--timeout-reject-ratio TIMEOUT_REJECT_RATIO]
                                           [--run-for RUN_FOR] [--num-cycles NUM_CYCLES] [--ttl-timeout TTL_TIMEOUT] [--database DATABASE] [--db-host DB_HOST] [--db-port DB_PORT]
                                           [--db-username DB_USERNAME] [--db-password DB_PASSWORD] [--db-name DB_NAME] [--service-name SERVICE_NAME] [--run-flush]
                                           [--flask-host FLASK_HOST] [--flask-port FLASK_PORT]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Specify the server host
  --admin-port ADMIN_PORT
                        Specify the server admin port
  --public-port PUBLIC_PORT
                        Specify the server public port
  --clients CLIENTS     Specify number of clients
  --clients-max-time CLIENTS_MAX_TIME
                        Max time assigned to client creation (in seconds)
  --login-failure-rate LOGIN_FAILURE_RATE
                        Specify (in percentage) the login failure rate
  --consent-failure-rate CONSENT_FAILURE_RATE
                        Specify (in percentage) the consent failure rate
  --timeout-reject-ratio TIMEOUT_REJECT_RATIO
                        Specify (in percentage) the timeout rate of a client appose to a client rejecting
  --run-for RUN_FOR     Specify number of minutes the tester should run for (no. clients)/(no. minutes)= no.clients/pm
  --num-cycles NUM_CYCLES
                        Specify the number of cycles the tester should run for.
  --ttl-timeout TTL_TIMEOUT
                        Specify the ttl timeout in seconds.
  --database DATABASE   The database which should be queried, e.g. postgresql or mysql
  --db-host DB_HOST     The database ip
  --db-port DB_PORT     The database port
  --db-username DB_USERNAME
                        The database username
  --db-password DB_PASSWORD
                        The database password
  --db-name DB_NAME     The database name e.g. hydra
  --service-name SERVICE_NAME
                        The service being tested (will be saved in sqlite db)
  --run-flush           Run the flush command after each cycle
  --flask-host FLASK_HOST
                        Specify the flask server host e.g. default: 127.0.0.1
  --flask-port FLASK_PORT
```

#### Server config

Run `python3 main.py server -h`

```shell
    usage: Hydra Database growth tester server [-h] [--host HOST] [--port PORT]
    
    optional arguments:
      -h, --help   show this help message and exit
      --host HOST  Specify the server binding address e.g. default: 127.0.0.1
      --port PORT  Specify the server binding port e.g. default: 3000
```

### Basic flow

```python
import uuid
import requests
from authlib.integrations.requests_client import OAuth2Session
from urllib.parse import urlparse, parse_qs

client_id = str(uuid.uuid4())
client_secret = str(uuid.uuid4())

# Create the client
resp = requests.post('http://127.0.0.1:6445/clients',
                     json={'client_id': client_id,
                           'grant_types': ['authorization_code', 'refresh_token'],
                           'scope': 'openid offline',
                           'response_types': ['code'],
                           'redirect_uris': [
                               f'http://127.0.0.1:3000/login',
                               f'http://127.0.0.1:3000/consent']})

print('init client', resp)

# Init login
c = OAuth2Session(client_id=client_id, client_secret=client_secret,
                  scope='openid offline')

uri, state = c.create_authorization_url(f'http://127.0.0.1:6444/oauth2/auth',
                                        redirect_uri='http://127.0.0.1:3000/login')

s = requests.Session()

resp = s.get(uri, allow_redirects=False)
print('init login', resp.headers.get('location'))
print('init login', resp.cookies.get('oauth2_authentication_csrf_insecure'))

login_challenge = parse_qs(urlparse(resp.headers.get('location')).query)['login_challenge'][0]
print('login challenge', login_challenge)

# Login accept
resp = s.put(f'http://127.0.0.1:6445/oauth2/auth/requests/login/accept?login_challenge={login_challenge}',
             json={'subject': client_id})

print('login accept', resp.json())

resp2 = s.get(resp.json()['redirect_to'])

print('login redirect -> consent', resp2.url)
consent_challenge = parse_qs(urlparse(resp2.url).query)['consent_challenge'][0]
print('consent challenge', login_challenge)

# Consent init
resp = s.get(f'http://127.0.0.1:6445/oauth2/auth/requests/consent?consent_challenge={consent_challenge}',
             allow_redirects=False)
print('consent init', resp.text)

# === Either accept or ===
# Consent accept
resp = s.put(f'http://127.0.0.1:6445/oauth2/auth/requests/consent/accept?consent_challenge={consent_challenge}',
             json={})

print('consent accept', resp.text)

resp2 = s.get(resp.json()['redirect_to'])

print('consent redirect', resp2)

# === Reject ===

# Consent reject
resp = s.put(
    f'http://127.0.0.1:6445/oauth2/auth/requests/consent/reject?consent_challenge={consent_challenge}',
    json={})
print('consent reject', resp.text)
resp2 = s.get(resp.json()['redirect_to'])
print('consent redirect', resp2)

```