from typing import Optional

import pyuseragents
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.eth import AsyncEth

from src.models.bridge import BridgeConfig


async def create_super_bridge_tx(
        self,
        contract: Optional[AsyncContract],
        bridge_config: BridgeConfig,
        amount: int
):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://superbridge.app',
        'priority': 'u=1, i',
        'referer': 'https://superbridge.app/',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': pyuseragents.random(),
    }

    request_args = {} if self.proxy is None else {
        'proxy': self.proxy.proxy_url
    }

    to_chain_web3 = AsyncWeb3(
        provider=AsyncWeb3.AsyncHTTPProvider(
            endpoint_uri=bridge_config.to_chain.rpc,
            request_kwargs=request_args
        ),
        modules={'eth': (AsyncEth,)},
    )

    json_data = {
        'host': 'superbridge.app',
        'amount': str(amount),
        'fromChainId': str(bridge_config.from_chain.chain_id),
        'toChainId': str(bridge_config.to_chain.chain_id),
        'fromTokenAddress': '0x0000000000000000000000000000000000000000'
        if bridge_config.from_token.name == 'ETH' else bridge_config.from_token.address,
        'toTokenAddress': '0x0000000000000000000000000000000000000000'
        if bridge_config.to_token.name == 'ETH' else bridge_config.to_token.address,
        'fromTokenDecimals': 18,
        'toTokenDecimals': 18,
        'fromGasPrice': str(await self.web3.eth.gas_price),
        'toGasPrice': str(await to_chain_web3.eth.gas_price),
        'graffiti': 'superbridge',
        'recipient': self.wallet_address,
        'sender': self.wallet_address,
        'forceViaL1': False,
    }

    response_json, status = await self.make_request(
        method="POST",
        url="https://api.superbridge.app/api/v2/bridge/routes",
        headers=headers,
        json=json_data
    )
    if status == 200:
        transaction = response_json['results'][0]['result']['initiatingTransaction']
        to = transaction['to']

        last_block = await self.web3.eth.get_block('latest')
        max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
        base_fee = int(last_block['baseFeePerGas'] * 1.15)
        max_fee_per_gas = base_fee + max_priority_fee_per_gas

        tx = {
            'from': self.wallet_address,
            'value': int(transaction['value']),
            'to': self.web3.to_checksum_address(to),
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'data': transaction['data'],
            'chainId': await self.web3.eth.chain_id,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "maxFeePerGas": max_fee_per_gas
        }

        return tx, to

