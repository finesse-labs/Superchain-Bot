from typing import Callable

import pyuseragents
from aiohttp import ClientSession
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.contract import Contract

from src.models.swap import SwapConfig
from src.utils.request_client.curl_cffi_client import CurlCffiClient
from src.utils.user.utils import Utils
from src.models.contracts import ERC20


def get_defillama_url(
        swap_config: SwapConfig,
        wallet_address: ChecksumAddress,
        amount: int,
        chain_id: int
) -> str:
    src = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if swap_config.from_token.name == 'ETH' else swap_config.from_token.address
    dst = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if swap_config.to_token.name == 'ETH' else swap_config.to_token.address
    return f'https://api-defillama.1inch.io/v6.0/{chain_id}/swap?src={src}&dst={dst}&amount={str(amount)}&from={wallet_address}&slippage=0.3&referrer=0xa43C3EDe995AA058B68B882c6aF16863F18c5330&disableEstimate=true&excludedProtocols=PMM1,PMM2,PMM3,PMM4,PMM2MM1,PMM9,PMM8,PMM11,PMM8_2,PMM12,PMM15,PMM17,PMM18,PMM16,PMM20,PMM22,PMM23'


async def create_defillama_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: Contract,
        amount_out: int,
        amount: int
):
    data, address, value = await get_data(
        self,
        swap_config,
        amount,
    )

    tx = {
        'from': self.wallet_address,
        'value': int(value),
        'to': self.web3.to_checksum_address(address),
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'chainId': await self.web3.eth.chain_id,
        'gasPrice': await self.web3.eth.gas_price,
        'data': data,
    }
    return tx, address


async def get_data(self, swap_config, amount: int) -> tuple[str, str, str]:
    tls_client = CurlCffiClient(proxy=self.proxy)
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'user-agent': pyuseragents.random(),
        'origin': 'https://swap.defillama.com',
        'referer': 'https://swap.defillama.com/',
    }
    chain_id = await self.web3.eth.chain_id
    url = get_defillama_url(
        swap_config,
        self.wallet_address,
        amount,
        chain_id
    )

    response_json, status = await tls_client.make_request(
        method='GET',
        url=url,
        headers=headers
    )
    data = response_json['tx']['data']
    address = response_json['tx']['to']
    value = response_json['tx']['value']

    return data, address, value
