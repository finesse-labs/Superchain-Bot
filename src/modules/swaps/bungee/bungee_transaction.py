from asyncio import sleep
from time import time
from typing import Optional, Dict, Any

import pyuseragents
from loguru import logger
from sqlalchemy.util import await_only
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.types import TxParams
from eth_typing import Address, ChecksumAddress

from config import SLIPPAGE
from src.models.swap import SwapConfig
from src.utils.data.tokens import tokens
from src.utils.request_client.curl_cffi_client import CurlCffiClient


async def quote_transaction(
        self,
        swap_config: SwapConfig,
        wallet_address: ChecksumAddress,
        web3: AsyncWeb3,
        amount: int,
        tls_client: CurlCffiClient,
        headers: Dict[str, str]
):
    params = {
        'fromChainId': str(self.chain.chain_id),
        'toChainId': str(self.chain.chain_id),
        'fromTokenAddress': '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
        if swap_config.from_token.name == 'ETH' else swap_config.from_token.address.lower(),
        'toTokenAddress': '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
        if swap_config.to_token.name == 'ETH' else swap_config.to_token.address.lower(),
        'fromAmount': str(amount),
        'userAddress': wallet_address,
        'singleTxOnly': 'true',
        'bridgeWithGas': 'false',
        'sort': 'output',
        'defaultSwapSlippage': '0.5',
        'isContractCall': 'false',
    }
    response_json, status = await tls_client.make_request(
        method="GET",
        url='https://api.socket.tech/v2/quote',
        params=params,
        headers=headers
    )
    if status == 200:
        return response_json


async def build_tx(
        self,
        quote: Dict[str, Any],
        tls_client: CurlCffiClient,
        headers: Dict[str, str],
        web3: AsyncWeb3,
        wallet_address: ChecksumAddress
) -> Optional[tuple[Dict[str, Any], str]]:
    json_data = {
        'route': quote['result']['routes'][0]
    }
    response_json, status = await tls_client.make_request(
        method="POST",
        url='https://api.socket.tech/v2/build-tx',
        headers=headers,
        json=json_data
    )
    if status == 201:
        transaction = response_json['result']

        tx = {
            'chainId': self.chain.chain_id,
            'to': web3.to_checksum_address(transaction['txTarget']),
            'from': wallet_address,
            'value': int(transaction['value'], 16),
            'data': transaction['txData'],
            'nonce': await web3.eth.get_transaction_count(wallet_address),
            'gasPrice': await web3.eth.gas_price,
        }

        tx.update({'gas': await web3.eth.estimate_gas(tx)})

        return tx, transaction['txTarget']


async def create_bungee_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: AsyncContract,
        amount_out: int,
        amount: int,
) -> Optional[tuple[TxParams | Dict, Optional[str]]]:
    tls_client = CurlCffiClient(proxy=self.proxy)

    headers = {
        'accept': 'application/json',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'api-key': '1b2fd225-062f-41aa-8c63-d1fef19945e7',
        'origin': 'https://www.bungee.exchange',
        'priority': 'u=1, i',
        'referer': 'https://www.bungee.exchange/',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': pyuseragents.random(),
    }

    quote = await quote_transaction(
        self,
        swap_config,
        self.wallet_address,
        self.web3,
        amount,
        tls_client,
        headers
    )
    if not quote:
        logger.error(f'[{self.wallet_address}] | Failed to quote bungee transaction')
        return None

    approval_data = quote['result']['routes'][0]['userTxs'][0]['approvalData']
    if approval_data:
        await self.approve_token(
            amount,
            self.private_key,
            self.config.from_token.address,
            approval_data['allowanceTarget'],
            self.wallet_address,
            self.web3
        )
        await sleep(3)

    return await build_tx(self, quote, tls_client, headers, self.web3, self.wallet_address)
