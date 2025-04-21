from typing import Callable

import pyuseragents
from aiohttp import ClientSession
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.contract import Contract, AsyncContract
from web3.types import TxParams

from src.models.swap import SwapConfig
from src.utils.request_client.curl_cffi_client import CurlCffiClient


async def create_sushiswap_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: AsyncContract,
        amount_out: int,
        amount: int
):
    data, address, gas, gas_price, value = await get_data(
        self,
        swap_config,
        amount,
    )
    tx = {
        'chainId': self.chain.chain_id,
        'to': self.web3.to_checksum_address(address),
        'from': self.wallet_address,
        'value': int(value),
        'data': data,
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'gasPrice': gas_price,
        'gas': int(gas),
    }
    return tx, address


async def get_data(self, swap_config: SwapConfig, amount: int) -> tuple[str, str, str, int, str]:
    tls_client = CurlCffiClient(proxy=self.proxy)
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'user-agent': pyuseragents.random(),
        'origin': 'https://www.sushi.com',
        'referer': 'https://www.sushi.com/',
    }
    params = {
        'referrer': 'sushi',
        'tokenIn': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if swap_config.from_token.name.upper() == 'ETH'
        else swap_config.from_token.address,
        'tokenOut': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if swap_config.to_token.name.upper() == 'ETH'
        else swap_config.to_token.address,
        'amount': str(amount),
        'maxSlippage': '0.005',
        'sender': self.wallet_address,
        'recipient': self.wallet_address,
        'feeReceiver': '0xca226bd9c754F1283123d32B2a7cF62a722f8ADa',
        'fee': '0.0025',
        'feeBy': 'output',
    }

    response_json, status = await tls_client.make_request(
        method="GET",
        # url=f'https://api.sushi.com/swap/v5/{str(await web3.eth.chain_id)}',
        url=f'https://api.sushi.com/swap/v6/{str(await self.web3.eth.chain_id)}',
        headers=headers,
        params=params,
    )
    data = response_json['tx']['data']
    address = response_json['tx']['to']
    gas = response_json['tx']['gas']
    gas_price = response_json['tx']['gasPrice']
    value = response_json['tx']['value']
    return data, address, gas, gas_price, value
