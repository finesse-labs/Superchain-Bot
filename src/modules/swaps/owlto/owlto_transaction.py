from typing import Callable, Tuple, Any, Dict, Optional, Union

import pyuseragents
from web3.contract import AsyncContract
from web3.types import TxParams

from src.models.contracts import ERC20
from src.models.swap import SwapConfig
from src.utils.request_client.curl_cffi_client import CurlCffiClient
from src.utils.user.utils import Utils


async def create_owlto_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: AsyncContract,
        amount_out: int,
        amount: int
) -> Tuple[Dict[str, Any], str]:
    data, address, gas = await get_data(
        self,
        swap_config,
        amount
    )
    tx = {
        'from': self.wallet_address,
        'value': amount if swap_config.from_token.name.upper() == 'ETH' else 0,
        'to': self.web3.to_checksum_address(address),
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'chainId': await self.web3.eth.chain_id,
        'gasPrice': await self.web3.eth.gas_price,
        'data': data,
        'gas': int(gas)
    }
    return tx, address


async def get_data(self, swap_config: SwapConfig, amount: int) -> Tuple[str, str, str]:
    tls_client = CurlCffiClient(proxy=self.proxy)
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'user-agent': pyuseragents.random(),
        'origin': 'https://owlto.finance',
        'referer': 'https://owlto.finance/swap',
    }
    from_token_contract = Utils.load_contract(
        address=swap_config.from_token.address,
        web3=self.web3,
        abi=ERC20.abi
    )
    from_decimals = await from_token_contract.functions.decimals().call()

    to_token_contract = Utils.load_contract(
        address=swap_config.to_token.address,
        web3=self.web3,
        abi=ERC20.abi
    )
    to_decimals = await to_token_contract.functions.decimals().call()
    # await self.approve_token(
    #     amount=swap_config.amount,
    #     private_key=private_key,
    #     from_token_address=swap_config.from_token.address,
    #     spender='0x89d43d991F47924Dd47C9b6a7Fa17C6a15091999',
    #     address_wallet=self.wallet_address,
    #     web3=self.web3
    #
    # )
    json_data = {
        'source_chain_id': str(await self.web3.eth.chain_id),
        'target_chain_id': str(await self.web3.eth.chain_id),
        'user': self.wallet_address,
        'recipient': self.wallet_address,
        'token_in': {
            'address': '0x0000000000000000000000000000000000000000' if swap_config.from_token.name.upper() == 'ETH'
            else swap_config.from_token.address,
            'decimals': from_decimals,
            'icon': '',
            'name': swap_config.from_token.name.upper(),
        },
        'token_out': {
            'address': '0x0000000000000000000000000000000000000000' if swap_config.to_token.name.upper() == 'ETH'
            else swap_config.to_token.address,
            'decimals': to_decimals,
            'icon': '',
            'name': swap_config.to_token.name.upper(),
        },
        'slippage': '0.05',
        'amount': str(amount),
        'channel': 98675412,
    }
    response_json, status = await tls_client.make_request(
        method="POST",
        url='https://owlto.finance/api/swap_api/v1/make_swap',
        headers=headers,
        json=json_data
    )
    data = response_json['data']['contract_calls'][0]['calldata']
    address = response_json['data']['contract_calls'][0]['contract']
    gas = response_json['data']['contract_calls'][0]['gas_limit']
    return data, address, gas
