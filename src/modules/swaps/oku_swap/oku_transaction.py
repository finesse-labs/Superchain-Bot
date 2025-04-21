from typing import Callable, Optional, Any

import pyuseragents
from eth_account.messages import encode_typed_data
from web3 import AsyncWeb3
from web3.contract import Contract
from loguru import logger

from src.models.swap import SwapConfig
from src.models.contracts import ERC20
from src.utils.request_client.curl_cffi_client import CurlCffiClient


async def create_oku_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: Contract,
        amount_out: int,
        amount: int
) -> tuple[Any, Any]:
    data, address, value, approvee, gas = await get_data(
        self,
        self.config,
        amount,
        self.private_key
    )
    if not data:
        return None, None
    tx = {
        'from': self.wallet_address,
        'value': value,
        'to': self.web3.to_checksum_address(address),
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'chainId': await self.web3.eth.chain_id,
        'gasPrice': await self.web3.eth.gas_price,
        'data': data,
        'gas': int(gas)
    }

    return tx, approvee


async def get_permit_signature(data: dict, web3: AsyncWeb3, private_key: str):
    account = web3.eth.account.from_key(private_key)
    full_message = data['typedData'][0]['payload']
    structured_msg = encode_typed_data(full_message=full_message)
    signed_data = account.sign_message(structured_msg)
    signature = signed_data.signature.hex()
    # v, r, s = signed_data.v, signed_data.r, signed_data.s
    # token_contract = web3.eth.contract(address=web3.to_checksum_address(from_token_address), abi=ERC20.abi)

    return signature


async def request_permit(data: dict, web3: AsyncWeb3, private_key: str, coupon: dict, tls_client):
    headers = {
        'authority': 'canoe.v2.icarus.tools',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://oku.trade',
        'referer': 'https://oku.trade/',
        'traceparent': '00-65b255732312bc0637a2282b3757f1f2-b4b85ca56b8a7d39-01',
        'user-agent': pyuseragents.random(),
    }
    signature = await get_permit_signature(data, web3, private_key)
    data['typedData'][0]['signature'] = '0x' + signature
    json_data = {
        'coupon': coupon,
        'signingRequest': data
    }

    response_json, status = await tls_client.make_request(
        method='POST',
        url='https://canoe.v2.icarus.tools/market/usor/execution_information',
        headers=headers,
        json=json_data
    )

    data = response_json['trade']['data']
    value = int(response_json['trade']['value'], 16)
    to = response_json['trade']['to']
    return data, value, to


async def get_data(self, swap_config: SwapConfig, amount: int, private_key: str):
    tls_client = CurlCffiClient(proxy=self.proxy)
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'user-agent': pyuseragents.random(),
        'origin': 'https://oku.trade',
        'referer': 'https://oku.trade/',
    }
    url = 'https://canoe.v2.icarus.tools/market/usor/swap_quote'

    decimals = 18
    if not swap_config.from_token.name.upper() == 'ETH':
        contract = self.web3.eth.contract(address=swap_config.from_token.address, abi=ERC20.abi)
        decimals = await contract.functions.decimals().call()

    adjusted_amount = int(amount) // 10 ** (decimals // 2) * 10 ** (decimals // 2)
    formatted_amount = f"{adjusted_amount / 10 ** decimals:.18f}".rstrip('0').rstrip('.')
    if swap_config.from_token.name not in ['ETH', 'LISK']:
        formatted_amount = f"{adjusted_amount / 10 ** decimals:.{decimals}f}"
    if swap_config.from_token.name.upper() == 'WBTC':
        formatted_amount = f"{amount / 10 ** decimals:.8f}".rstrip('0').rstrip('.')

    json_data = {
        'chain': 'optimism' if self.chain.chain_name == 'OP' else self.chain.chain_name.lower(),
        'account': self.wallet_address,
        'inTokenAddress': '0x0000000000000000000000000000000000000000' if swap_config.from_token.name.upper() == 'ETH'
        else swap_config.from_token.address,
        'outTokenAddress': '0x0000000000000000000000000000000000000000' if swap_config.to_token.name.upper() == 'ETH'
        else swap_config.to_token.address,
        'isExactIn': True,
        'slippage': 50,
        'inTokenAmount': str(formatted_amount),
    }
    attempt = 0
    while True:
        attempt += 1
        if attempt > 2:
            logger.info("Failed to get response after 2 attempts")
            break
        try:
            response_json, status = await tls_client.make_request(
                method='POST',
                url=url,
                headers=headers,
                json=json_data
            )
            gas = int(response_json['fees']['gas'])  # если перестанет воркать, то в этом проблема
            if 'signingRequest' in response_json:
                if swap_config.from_token.name != 'ETH':
                    approvee = response_json['coupon']['raw']['executionInformation']['approvals'][0]['approvee']
                    coupon = response_json['coupon']
                    signing_request = response_json['signingRequest']
                    data, value, to = await request_permit(data=signing_request,
                                                           coupon=coupon,
                                                           web3=self.web3,
                                                           private_key=private_key,
                                                           tls_client=tls_client)
                    return data, to, value, approvee, gas
            data = response_json['coupon']['raw']['quote']['trade']['data']
            address = response_json['coupon']['raw']['quote']['trade']['to']
            value = int(response_json['coupon']['raw']['quote']['trade']['value'], 16)
            approvee = None
            if not swap_config.from_token.name == 'ETH':
                approvee = response_json['coupon']['raw']['executionInformation']['approvals'][0]['approvee']
            return data, address, value, approvee, gas
        except (KeyError, TypeError):
            logger.warning(f"Route [{swap_config.from_token.name} => {swap_config.to_token.name}] not found")
            return None, None, None, None, None
