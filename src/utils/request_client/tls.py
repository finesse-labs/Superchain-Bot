from typing import Dict, Any

import tls_client

from src.utils.proxy_manager import Proxy


class TlsClient:
    def __init__(self, proxy: Proxy | None):
        self.session = self.create_session(proxy)

    @staticmethod
    def create_session(proxy: Proxy | None):
        session = tls_client.Session(
            random_tls_extension_order=True,
        )

        session.proxies.update({
            'http': proxy.proxy_url if proxy else None,
            'https': proxy.proxy_url if proxy else None
        })

        return session

    def get_fingerprint(self):
        response = self.session.get("https://tls.browserleaks.com/json")
        return response.json()

    def make_request(
            self,
            method: str = 'GET',
            url: str = None,
            headers: Dict[str, Any] = None,
            data: str = None,
            json: Dict[str, Any] = None,
            params: Dict[str, Any] = None,
            cookies: Dict[str, Any] = None
    ):
        response = self.session.execute_request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            json=json,
            cookies=cookies
        )
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            return response.text, response.status_code