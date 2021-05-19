import logging
from math import floor

from tests import Tester

logger = logging.getLogger('db_growth_test')


class DBGrowth:

    def __init__(self, tester: Tester):
        self.tester = tester

    def run(self):
        """
        Run in sequence the following flow
        - Create oauth2 clients
        - Initialise login
        - Accept some login
        - Accept some consent
        - Reject some login
        - Reject some consent
        - Wait for login-consent timeout
        - Run flush(?)
        :return:
        """
        # checking if services are alive
        self.tester.patience_init()

        for c in range(0, self.tester.config["num_cycles"]):
            logger.info(f'Running Cycle {c}')
            self.tester.working_data['cycle'] = c

            logger.info("Initialising clients...")
            oauth_clients = self.tester.initialise_clients()
            self.tester.generate_report("clients_created")

            self.tester.registered_clients()

            self.tester.initialise_logins(clients=oauth_clients)
            self.tester.generate_report("client_login_init")
            # remove failed oauth clients
            oauth_clients = [x for x in oauth_clients if 'login_challenge' in x]
            c = floor(len(oauth_clients) * (self.tester.config['login_failure_rate'] / 100))

            clients_reject = oauth_clients[0:c]
            clients_accept = oauth_clients[len(clients_reject):len(oauth_clients)]
            clients_timeout = clients_reject[
                              0:floor(len(clients_reject) * (self.tester.config['timeout_reject_ratio'] / 100))]
            # clients rejecting the auth would probably be less than those timing out (or never completing the request)
            clients_reject = clients_reject[len(clients_timeout):len(clients_reject)]

            # Accept Login
            accepted_clients = [x for x in self.tester.accept_login(clients=clients_accept) if x is not None]
            self.tester.generate_report('after_client_login_accept')

            c = floor(len(clients_accept) * (self.tester.config['consent_failure_rate'] / 100))
            clients_reject_consent = clients_accept[0:c]
            clients_accept_consent = clients_accept[len(clients_reject_consent):len(clients_accept)]

            # Accept Consent
            self.tester.initialise_consent(clients=clients_accept_consent)
            self.tester.generate_report('after_client_consent_init')

            # Reject Login
            self.tester.reject_login(clients=clients_reject)
            self.tester.generate_report('after_client_login_reject')

            # Reject Consent
            self.tester.reject_consent(clients=clients_reject_consent)
            self.tester.generate_report('after_client_consent_reject')

            self.tester.run_flush()
