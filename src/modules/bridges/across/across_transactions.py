from typing import Optional, Callable, Dict, Any

import pyuseragents
from eth_typing import ChecksumAddress
from web3.contract import AsyncContract

from src.models.bridge import BridgeConfig
from src.models.contracts import AcrossBridgeData
from src.utils.data.tokens import tokens


async def get_quote(
        bridge_config: BridgeConfig,
        wallet_address: ChecksumAddress,
        amount: int,
        request_func: Callable
) -> Optional[Dict[str, Any]]:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=1, i',
        'referer': 'https://app.across.to/',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': pyuseragents.random(),
    }

    params = {
        'inputToken': '0x4200000000000000000000000000000000000006',
        'outputToken': '0x4200000000000000000000000000000000000006',
        'destinationChainId': str(bridge_config.to_chain.chain_id),
        'originChainId': str(bridge_config.from_chain.chain_id),
        'recipient': wallet_address,
        'amount': str(amount),
        'skipAmountLimit': 'true',
    }

    response_json, status = await request_func(
        method="GET",
        url='https://app.across.to/api/suggested-fees',
        params=params,
        headers=headers
    )
    if status == 200:
        return response_json


async def create_across_tx(
        self,
        contract: Optional[AsyncContract],
        bridge_config: BridgeConfig,
        amount: int
):
    quote = await get_quote(bridge_config, self.wallet_address, amount, self.make_request)

    contracts = {
        'BASE': '0x09aea4b2242abc8bb4bb78d537a67a245a7bec64',
        'OP': '0x6f26bf09b1c792e3228e5467807a900a503c0281',
        'ARB': '0xe35e9842fceaca96570b734083f4a58e8f7c5f2a'
    }
    contract = self.load_contract(
        address=contracts[bridge_config.from_chain.chain_name],
        web3=self.web3,
        abi=AcrossBridgeData.abi
    )

    tx = await contract.functions.depositV3(
        self.wallet_address,
        self.wallet_address,
        self.web3.to_checksum_address(tokens[bridge_config.from_chain.chain_name]['WETH']),
        self.web3.to_checksum_address(tokens[bridge_config.from_chain.chain_name]['WETH']),
        amount,
        amount - int(quote['relayFeeTotal']),
        bridge_config.to_chain.chain_id,
        self.web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
        int(quote['timestamp']),
        int(quote['fillDeadline']),
        0,
        b''
    ).build_transaction({
        'value': amount,
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'from': self.wallet_address,
        'gasPrice': await self.web3.eth.gas_price,
    })
    return tx, None
