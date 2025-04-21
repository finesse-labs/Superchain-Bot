import time
from typing import Optional

from eth_account.messages import encode_defunct
from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.utils.common.wrappers.decorators import retry
from src.utils.proxy_manager import Proxy
from src.utils.request_client.curl_cffi_client import CurlCffiClient
from src.utils.user.account import Account


class SuperAccount(Account, CurlCffiClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        CurlCffiClient.__init__(self, proxy=proxy)

        self.headers = {
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://account.superchain.eco',
            'priority': 'u=1, i',
            'referer': 'https://account.superchain.eco/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-storage-access': 'active',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

    async def get_nonce(self) -> Optional[str]:
        nonce, status = await self.make_request(
            method="GET",
            url='https://scsa-backend-production.up.railway.app/auth/nonce',
            headers=self.headers,
            return_text=True
        )
        if status == 200:
            return nonce

    def get_signature(self, msg: str) -> str:
        signed_message = self.web3.eth.account.sign_message(
            encode_defunct(text=msg), private_key=self.private_key
        )
        signature = signed_message.signature.hex()
        return '0x' + signature

    async def auth(self):
        nonce = await self.get_nonce()
        current_time = time.time()
        gmt_time = time.gmtime(current_time)
        iso_time = (
            f"{gmt_time.tm_year}-"
            f"{gmt_time.tm_mon:02d}-"
            f"{gmt_time.tm_mday:02d}T"
            f"{gmt_time.tm_hour:02d}:"
            f"{gmt_time.tm_min:02d}:"
            f"{gmt_time.tm_sec:02d}"
            f".{int((current_time % 1) * 1000):03d}Z"
        )
        msg = f'account.superchain.eco wants you to sign in with your Ethereum account:\n{self.wallet_address}\n\nWelcome to SuperAccounts!\nPlease sign this message\n\nURI: https://account.superchain.eco\nVersion: 1\nChain ID: 10\nNonce: {nonce}\nIssued At: {iso_time}'
        signature = self.get_signature(msg)

        json_data = {
            'message': msg,
            'signature': signature
        }
        response = await self.make_request(
            method="POST",
            url="https://scsa-backend-production.up.railway.app/auth/verify",
            headers=self.headers,
            json=json_data,
            return_full_response=True
        )
        set_cookie = response.headers.get('set-cookie')
        cookie_parts = set_cookie.split(';')[0]
        cookie_name, cookie_value = cookie_parts.split('=', 1)
        self.headers['Cookie'] = f'{cookie_name}={cookie_value}'

    async def get_safe_address(self):
        response_json, status = await self.make_request(
            method="GET",
            url=f'https://safe-client.safe.global/v1/owners/{self.wallet_address}/safes'
        )
        op_safes = response_json['10']
        if len(op_safes) == 0:
            logger.error(f'[{self.wallet_address}] | You must register first')
            return None
        elif len(op_safes) == 1:
            return op_safes[0]

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def claim_badges(self) -> Optional[bool]:
        await self.auth()
        logger.success(f'[{self.wallet_address}] | Successfully authenticated!')
        safe_address = await self.get_safe_address()
        if not safe_address:
            return None

        response_json, status = await self.make_request(
            method="POST",
            url=f'https://scsa-backend-production.up.railway.app/api/user/{safe_address}/badges/claim',
            headers=self.headers,
        )
        if response_json['updatedBadges']:
            tx_hash = response_json["hash"]
            logger.success(
                f'[{self.wallet_address}] | Successfully claimed badges! '
                f'| TX: https://optimistic.etherscan.io/tx/{tx_hash}'
            )
            return True
        else:
            logger.warning(f'[{self.wallet_address}] | There are no badges to claim.')
