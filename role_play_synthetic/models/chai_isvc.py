import requests

from role_play_synthetic.models.base import Model


class ChaiISVCModel(Model):

    def __init__(self, endpoint_url):
        super(ChaiISVCModel, self).__init__()
        self.endpoint_url = endpoint_url

    def generate(self, prompt: str, generation_params: dict):
        payload = {'instances': [{'text': prompt, 'generation_params': generation_params}]}
        response = _get_endpoint_response_with_fallback(self.endpoint_url, payload)
        response = _format_response(response)
        if prompt.endswith("*"):
            response = "*" + response
        return response


def _get_endpoint_response_with_fallback(endpoint_url, payload):
    resp = requests.post(endpoint_url, json=payload, timeout=60)
    assert resp.status_code == 200
    prediction = resp.json()['predictions'][0]
    return prediction


def _format_response(text):
    text = text.replace('\*\*', '*')
    text = text.replace('\*', '*')
    return text.strip()
