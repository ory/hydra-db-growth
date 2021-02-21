import ory_hydra_client as hydra
import uuid


class AdminHydra:

    def __init__(self, client: hydra.ApiClient):
        self.client = client

    def gen_client(self):
        client_id = str(uuid.uuid4())
        client_secret = str(uuid.uuid4())

        resp = self.client.call_api(resource_path='/clients', method='POST',
                                    body={'client_id': client_id,
                                          'grant_types': ['authorization_code', 'refresh_token'],
                                          'scope': 'openid offline',
                                          'response_types': ['code'],
                                          'redirect_uris': ['http://127.0.0.1:3000/login']})
        if resp[1] == 201:
            return {'client_id': client_id, 'client_secret': client_secret}
        else:
            return None
