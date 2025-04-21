from collections.abc import Callable

import pyuseragents
from aiohttp import ClientSession
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.contract import Contract, AsyncContract
from web3.types import TxParams

from loguru import logger
from src.models.swap import SwapConfig
from src.utils.request_client.curl_cffi_client import CurlCffiClient


async def create_relay_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: AsyncContract,
        amount_out: int,
        amount: int
):
    steps = await get_data(
        self,
        swap_config,
        amount,
    )
    tx = {}
    for transaction in steps:
        if transaction['id'] == 'approve':
            continue
            # tx = {
            #     'from': self.wallet_address,
            #     'to': self.web3.to_checksum_address(transaction['items'][0]['data']['to']),
            #     'data': transaction['items'][0]['data']['data'],
            #     'value': transaction['items'][0]['data']['value'],
            #     'chainId': await self.web3.eth.chain_id,
            #     'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            #     'gas': transaction['items'][0]['data']['gas'],
            #     'gasPrice': await self.web3.eth.gas_price
            # }
            # tx_hash = await self.sign_transaction(tx)
            # confirmed = await self.wait_until_tx_finished(tx_hash)
            # if confirmed:
            #     logger.success(f'Approving token...')
        else:
            tx = {
                'from': self.wallet_address,
                'to': self.web3.to_checksum_address(transaction['items'][0]['data']['to']),
                'data': transaction['items'][0]['data']['data'],
                'value': int(transaction['items'][0]['data']['value']),
                'chainId': await self.web3.eth.chain_id,
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'gas': int(transaction['items'][0]['data']['gas']),
                'gasPrice': await self.web3.eth.gas_price
            }
            return tx, tx['to']


async def get_data(self, swap_config, amount: int) -> tuple[str, str]:
    tls_client = CurlCffiClient(proxy=self.proxy)
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'user-agent': pyuseragents.random(),
        'origin': 'https://relay.link',
        'referer': 'https://relay.link/',
    }
    chain_id = await self.web3.eth.chain_id
    json_data = {
        'user': self.wallet_address,
        'originChainId': chain_id,
        'destinationChainId': chain_id,
        'originCurrency': '0x0000000000000000000000000000000000000000' if swap_config.from_token.name.upper() in [
            'ETH', 'WETH']
        else swap_config.from_token.address,
        'destinationCurrency': '0x0000000000000000000000000000000000000000' if swap_config.to_token.name.upper() in [
            'ETH', 'WETH']
        else swap_config.to_token.address,
        'recipient': self.wallet_address,
        'tradeType': 'EXACT_INPUT',
        'amount': str(amount),
        'referrer': 'relay.link/swap',
        'useExternalLiquidity': False,
    }

    response_json, status = await tls_client.make_request(
        method='POST',
        url='https://api.relay.link/quote',
        headers=headers,
        json=json_data
    )
    steps = response_json['steps']
    return steps
