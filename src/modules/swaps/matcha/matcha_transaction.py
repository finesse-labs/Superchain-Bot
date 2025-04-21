from typing import Optional, Dict, Any

import pyuseragents
from web3.contract import AsyncContract
from web3.types import TxParams

from src.models.swap import SwapConfig
from src.utils.request_client.curl_cffi_client import CurlCffiClient


async def get_gas_params(headers: Dict[str, Any], tls_client: CurlCffiClient, chain_id: int):
    params = {
        'chainId': str(chain_id),
    }
    response_json, status = await tls_client.make_request(
        method="GET",
        url='https://matcha.xyz/api/gas',
        params=params,
        headers=headers
    )
    if status == 200:
        return response_json['suggested']['maxFeePerGas']


async def create_matcha_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: AsyncContract,
        amount_out: int,
        amount: int,
) -> Optional[tuple[TxParams | Dict, Optional[str]]]:
    tls_client = CurlCffiClient(proxy=self.proxy)

    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sentry-trace': 'dbe3e4878345458abac4a5e2febec211-a800ff5df6e777c1-0',
        'user-agent': pyuseragents.random(),
    }
    gas_price = await get_gas_params(headers, tls_client, self.chain.chain_id)

    params = {
        'chainId': str(self.chain.chain_id),
        'buyToken': '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
        if swap_config.to_token.name == 'ETH' else swap_config.to_token.address.lower(),
        'sellToken': '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
        if swap_config.from_token.name == 'ETH' else swap_config.from_token.address.lower(),
        'sellAmount': str(amount),
        'taker': self.wallet_address,
        'slippageBps': '50',
        'gasPrice': gas_price,
    }
    response_json, status = await tls_client.make_request(
        method="GET",
        url='https://matcha.xyz/api/swap/quote',
        params=params,
        headers=headers
    )
    if status == 200:
        transaction = response_json['transaction']
        tx = {
            'chainId': self.chain.chain_id,
            'to': self.web3.to_checksum_address(transaction['to']),
            'from': self.wallet_address,
            'value': int(transaction['value']),
            'data': transaction['data'],
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'gasPrice': int(transaction['gasPrice']),
            'gas': int(transaction['gas']),
        }
        return tx, transaction['to']
