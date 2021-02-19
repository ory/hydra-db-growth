import ory_hydra_client as hydra
import uuid


def gen_client(admin_client: hydra.ApiClient):
    client_id = str(uuid.uuid4())
    return admin_client.call_api(resource_path='/clients', method='POST', body={'client_id': client_id})
