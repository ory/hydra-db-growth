import logging
import os
from datetime import datetime

import requests

import database
import utils
from hydra.hydra_cli_client import flush
from hydra.hydra_http_client import create_client, health, init_login, accept_login, init_consent, reject_login, \
    reject_consent

logger = logging.getLogger('tester')


class Tester:

    def __init__(self, config, db, external_db, working_data, concurrency_workers=100):
        self._config = config
        self._db = db
        self._external_db = external_db
        self._working_data = working_data
        self.workers = concurrency_workers

    @property
    def config(self):
        return self._config

    @property
    def db(self):
        return self._db

    @property
    def external_db(self):
        return self._external_db

    @property
    def working_data(self):
        return self._working_data

    def webserver_health(self):
        wait_time = 2
        max_time = 100

        while True:
            resp = requests.get(f'http://{self.config["flask_host"]}:{self.config["flask_port"]}/ping')
            if resp.ok:
                break

            wait_time *= 2
            if wait_time > max_time:
                logger.error(
                    f'Ending tester due to initialisation failure. Wait time has exceeded max_time: '
                    f'({wait_time} > {max_time})')
                raise Exception(
                    f'could not connect to webserver instance on http://{self.config["flask_host"]}:{self.config["flask_port"]}/ping)'
                )

    def patience_init(self):
        wait_time = 2
        max_time = 100
        while True:
            if health(self.config['host'], self.config['public_port']):
                break

            wait_time *= 2
            if wait_time > max_time:
                logger.error(
                    f'Ending tester due to initialisation failure. Wait time has exceeded max_time: '
                    f'({wait_time} > {max_time})')
                raise Exception(
                    f'could not connect to hydra instance on http://{self.config["host"]}:{self.config["public_port"]}...')

    def initialise_clients(self):
        concurrent = utils.Concurrent(max_workers=self.workers)
        [concurrent.add_future(create_client, self.config, self.config['host'], self.config['admin_port']) for i in
         range(0, self.config["clients"])]
        return concurrent.run()

    def initialise_logins(self, clients):
        concurrent = utils.Concurrent(max_workers=self.workers)
        [concurrent.add_future(init_login,
                               client=c,
                               host=self.config['host'],
                               port=self.config['public_port']) for c in clients]
        return concurrent.run()

    def accept_login(self, clients):
        concurrent = utils.Concurrent(max_workers=self.workers)
        [concurrent.add_future(accept_login, client=c, host=self.config['host'], port=self.config['admin_port']) for c
         in clients]
        return concurrent.run()

    def initialise_consent(self, clients):
        concurrent = utils.Concurrent(max_workers=self.workers)
        [concurrent.add_future(init_consent, client=c, host=self.config['host'], port=self.config['admin_port']) for c
         in clients]
        return concurrent.run()

    def reject_login(self, clients):
        concurrent = utils.Concurrent(max_workers=self.workers)
        [concurrent.add_future(reject_login, client=c, host=self.config['host'], port=self.config['admin_port']) for c
         in clients]
        return concurrent.run()

    def reject_consent(self, clients):
        concurrent = utils.Concurrent(max_workers=self.workers)
        [concurrent.add_future(reject_consent, client=c, host=self.config['host'], port=self.config['admin_port']) for c
         in clients]
        return concurrent.run()

    def generate_report(self, action):
        self.working_data['results'] = db_sizes = self.external_db.gen_hydra_report()
        logger.info(f'SIZE {self.working_data["results"]}')
        database.save_result_to_sqlite(self.db, action, self.working_data)
        logger.info(f'Cycle: {self.working_data["cycle"]} | Action: {action} | {datetime.now()} | db_size: {db_sizes}')

    def registered_clients(self):
        self.working_data['registered_clients'] = self.external_db.get_registered_clients()
        logger.info(f'registered clients {self.working_data["registered_clients"]}')

    def run_flush(self):
        if self.config['run_flush']:
            ok = os.system(".build/hydra/hydra janitor -e")
            logger.info(ok)
            flush(self.external_db.get_dsn(), True, True)
            self.generate_report('after_flush')
        else:
            logger.warning("flush skipped by config")
