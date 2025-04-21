from typing import Dict, Any
from loguru import logger
import random

from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector

from src.utils.data.helper import proxies
from src.utils.proxy_manager import Proxy


class RequestClient:
    def __init__(self, proxy: Proxy | None):
        self.session = None
        self.create_session(proxy)

    def create_session(self, proxy: Proxy | None):
        try:
            connector = ProxyConnector.from_url(proxy.proxy_url) if proxy else TCPConnector(verify_ssl=False)
            self.session = ClientSession(connector=connector)
        except Exception as ex:
            logger.error(f"Failed to create session with proxy. | Error: {ex}")
            random_proxy = f"http://{random.choice(proxies)}" if proxies else None

            if random_proxy:
                logger.info(f"Retrying with a random proxy...")
                self.create_session(Proxy(proxy_url=random_proxy, change_link=None))
            else:
                logger.error("No proxies available for retry.")
                raise RuntimeError("Failed to create a session and no proxies are available.")

    async def make_request(
            self,
            method: str = 'GET',
            url: str = None,
            headers: Dict[str, Any] = None,
            data: str = None,
            json: Dict[str, Any] = None,
            params: Dict[str, Any] = None,
            cookies: Dict[str, Any] = None
    ):
        try:
            async with self.session.request(
                    method=method, url=url, headers=headers, data=data, params=params, json=json, cookies=cookies
            ) as response:
                if response.status in [200, 201, 202]:
                    response_json = await response.json()
                    return response_json, response.status
                else:
                    response_text = await response.text()
                    logger.error(f"Request failed with status: {response.status}")
                    return response_text, response.status
        except Exception as ex:
            logger.error(f"Something went wrong during request: {ex}")
            return None, None
