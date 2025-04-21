from typing import Optional, Callable, Any, Dict

import pyuseragents
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from web3.types import TxParams

from src.models.bridge import BridgeConfig


async def create_relay_tx(
        self,
        contract: Optional[AsyncContract],
        bridge_config: BridgeConfig,
        amount: int
) -> Optional[tuple[TxParams | Dict, Optional[str]]]:
    steps = await get_data(
        self.web3,
        bridge_config.from_token.name,
        bridge_config.to_token.name,
        bridge_config.from_token.address,
        bridge_config.to_token.address,
        amount,
        self.wallet_address,
        self.make_request,
        bridge_config.to_chain.chain_id,
        bridge_config
    )
    for transaction in steps:
        if transaction['id'] == 'approve':
            continue
        tx = {
            'from': self.wallet_address,
            'value': amount if
            bridge_config.from_token.name.upper() == bridge_config.from_chain.native_token.upper() else 0,
            'to': self.web3.to_checksum_address(transaction['items'][0]['data']['to']),
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'chainId': await self.web3.eth.chain_id,
            'gasPrice': int(await self.web3.eth.gas_price * 1.2),
            'data': transaction['items'][0]['data']['data']
        }
        return tx, None


async def get_data(
        web3: AsyncWeb3, from_token: str, to_token: str, from_token_address: str, to_token_address: str,
        amount: int, wallet_address: ChecksumAddress, request_function: Callable, destination_chain_id: int,
        bridge_config: BridgeConfig
) -> list[Any]:
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'user-agent': pyuseragents.random(),
        'origin': 'https://relay.link',
        'referer': 'https://relay.link/'
    }
    json_data = {
        'user': wallet_address,
        'originChainId': await web3.eth.chain_id,
        'destinationChainId': destination_chain_id,
        'originCurrency': '0x0000000000000000000000000000000000000000' if
        from_token.upper() == bridge_config.from_chain.native_token.upper() else from_token_address,
        'destinationCurrency': '0x0000000000000000000000000000000000000000' if
        to_token.upper() == bridge_config.to_chain.native_token.upper() else to_token_address,
        'recipient': wallet_address,
        'tradeType': 'EXACT_INPUT',
        'amount': str(amount),
        'referrer': 'relay.link/swap',
        'useExternalLiquidity': False,
    }

    try:
        response_json, status = await request_function(
            method='POST',
            url='https://api.relay.link/quote',
            headers=headers,
            json=json_data
        )
        if 'errorCode' in response_json:
            print(f"Ошибка: {response_json.get('message', 'Неизвестная ошибка')}")
            return

        steps = response_json['steps']
        return steps

    except Exception as e:
        exit(0)
