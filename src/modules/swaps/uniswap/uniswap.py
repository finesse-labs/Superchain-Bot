from asyncio import sleep
from typing import Optional, Dict, Any

from eth_account.messages import encode_typed_data
from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.models.chain import Chain
from src.models.swap import SwapConfig
from src.models.token import Token
from src.modules.swaps.uniswap.constants import UNISWAP_HEADERS
from src.utils.common.wrappers.decorators import retry
from src.utils.data.chains import chain_mapping

from src.utils.proxy_manager import Proxy
from src.utils.request_client.curl_cffi_client import CurlCffiClient
from src.utils.user.account import Account


class Uniswap(Account, CurlCffiClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            from_token: str | list[str],
            to_token: str | list[str],
            amount: float | list[float],
            use_percentage: bool,
            swap_percentage: float | list[float],
            swap_all_balance: bool,
            chain: Chain,
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy, rpc=chain.rpc)
        CurlCffiClient.__init__(self, proxy=proxy)

        self.swap_config = SwapConfig(
            from_token=Token(chain_name=chain.chain_name, name=from_token),
            to_token=Token(chain_name=chain.chain_name, name=to_token),
            amount=amount,
            use_percentage=use_percentage,
            swap_percentage=swap_percentage,
            swap_all_balance=swap_all_balance,
        )
        self.proxy = proxy
        self.chain = chain

    def __str__(self) -> str:
        return f'{self.__class__.__name__} | [{self.wallet_address}] | [{self.chain.chain_name}] |' \
               f' [{self.swap_config.from_token.name} => {self.swap_config.to_token.name}]'

    async def quote_swap(self, amount: int):
        json_data = {
            'amount': str(amount),
            'gasStrategies': [
                {
                    'limitInflationFactor': 1.15,
                    'displayLimitInflationFactor': 1.15,
                    'priceInflationFactor': 1.5,
                    'percentileThresholdFor1559Fee': 75,
                    'minPriorityFeeGwei': 2,
                    'maxPriorityFeeGwei': 9,
                },
            ],
            'swapper': self.wallet_address,
            'tokenIn': '0x0000000000000000000000000000000000000000' if self.swap_config.from_token.name == 'ETH'
            else self.swap_config.from_token.address,
            'tokenInChainId': self.chain.chain_id,
            'tokenOut': '0x0000000000000000000000000000000000000000' if self.swap_config.to_token.name == 'ETH'
            else self.swap_config.to_token.address,
            'tokenOutChainId': self.chain.chain_id,
            'type': 'EXACT_INPUT',
            'urgency': 'normal',
            'protocols': [
                'V4',
                'V3',
                'V2',
            ],
            'slippageTolerance': 2.5,
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://trading-api-labs.interface.gateway.uniswap.org/v1/quote',
            headers=UNISWAP_HEADERS,
            json=json_data
        )
        if status == 200:
            return response_json['quote'], response_json['permitData']

    async def get_json_data(self, quote: Dict[str, Any], permit_data: Optional[Dict[str, Any]]):
        json_data = {
            'quote': quote,
            'simulateTransaction': True,
            'refreshGasPrice': True,
            'gasStrategies': [
                {
                    'limitInflationFactor': 1.15,
                    'displayLimitInflationFactor': 1.15,
                    'priceInflationFactor': 1.5,
                    'percentileThresholdFor1559Fee': 75,
                    'minPriorityFeeGwei': 2,
                    'maxPriorityFeeGwei': 9,
                },
            ],
            'urgency': 'normal',
        }
        if permit_data:
            signature = self.get_permit_signature(permit_data)
            json_data.update({'permitData': permit_data})
            json_data.update({'signature': signature})
        return json_data

    def get_permit_signature(self, permit_data: Dict[str, Any]) -> str:
        to_sign = {
            "domain": {
                "name": "Permit2",
                "chainId": str(self.chain.chain_id),
                "verifyingContract": "0x000000000022d473030f116ddee9f6b43ac78ba3"
            },
            "message": permit_data['values'],
            "primaryType": "PermitSingle",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "PermitSingle": [
                    {"name": "details", "type": "PermitDetails"},
                    {"name": "spender", "type": "address"},
                    {"name": "sigDeadline", "type": "uint256"},
                ],
                "PermitDetails": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint160"},
                    {"name": "expiration", "type": "uint48"},
                    {"name": "nonce", "type": "uint48"}
                ]
            }
        }
        structured_msg = encode_typed_data(full_message=to_sign)
        signed_data = self.account.sign_message(structured_msg)
        signature = signed_data.signature.hex()
        return '0x' + signature

    async def get_transaction_params(self, quote: Dict[str, Any], permit_data: Optional[Dict[str, Any]]):
        json_data = await self.get_json_data(quote, permit_data)
        response_json, status = await self.make_request(
            method='POST',
            url='https://trading-api-labs.interface.gateway.uniswap.org/v1/swap',
            headers=UNISWAP_HEADERS,
            json=json_data
        )

        if status == 200:
            tx = {
                'chainId': self.chain.chain_id,
                'to': self.web3.to_checksum_address(response_json['swap']['to']),
                'from': self.wallet_address,
                'value': int(response_json['swap']['value'], 16),
                'data': response_json['swap']['data'],
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'gasPrice': int(response_json['swap']['gasPrice']),
                'gas': int(response_json['swap']['gasLimit']),
            }
            return tx

    async def check_approval(self, amount: int):
        json_data = {
            'walletAddress': self.wallet_address,
            'token': self.swap_config.from_token.address,
            'amount': str(amount),
            'chainId': self.chain.chain_id,
            'includeGasInfo': True,
            'gasStrategies': [
                {
                    'limitInflationFactor': 1.15,
                    'displayLimitInflationFactor': 1.15,
                    'priceInflationFactor': 1.5,
                    'percentileThresholdFor1559Fee': 75,
                    'minPriorityFeeGwei': 2,
                    'maxPriorityFeeGwei': 9,
                },
            ],
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://trading-api-labs.interface.gateway.uniswap.org/v1/check_approval',
            headers=UNISWAP_HEADERS,
            json=json_data
        )
        if status == 200:
            if response_json['approval']:
                transaction = {
                    'chainId': self.chain.chain_id,
                    'to': self.web3.to_checksum_address(self.swap_config.from_token.address),
                    'from': self.wallet_address,
                    'value': 0,
                    'data': response_json['approval']['data'],
                    'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                    'gasPrice': int(response_json['approval']['gasPrice']),
                    'gas': int(response_json['approval']['gasLimit']),
                }
                logger.debug(f'[{self.wallet_address}] | Approving token...')
                confirmed = None
                while True:
                    try:
                        tx_hash = await self.sign_transaction(transaction)
                        confirmed = await self.wait_until_tx_finished(tx_hash)
                        await sleep(2)
                    except Exception as ex:
                        if 'nonce' in str(ex):
                            transaction.update(
                                {'nonce': await self.web3.eth.get_transaction_count(self.wallet_address)})
                            continue
                        logger.error(f'Something went wrong {ex}')
                        return False
                    break
                if confirmed:
                    logger.success(f'[{self.wallet_address}] | Token approved')
                    return True

    async def get_transaction(self, amount: int):
        quote, permit_data = await self.quote_swap(amount)
        if not self.swap_config.from_token.name == 'ETH':
            await self.check_approval(amount)
            await sleep(4)
        return await self.get_transaction_params(quote, permit_data)

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def swap(self) -> Optional[bool | str]:
        is_native = self.swap_config.from_token.name.upper() == 'ETH'

        balance = await self.get_wallet_balance(
            is_native=is_native,
            address=self.swap_config.from_token.address
        )
        if balance == 0:
            logger.warning(f'Your {self.swap_config.from_token.name} balance is 0 | {self.wallet_address}')
            return 'ZeroBalance'

        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return False

        amount = await self.create_amount(
            is_native=is_native,
            from_token_address=self.swap_config.from_token.address,
            web3=self.web3,
            amount=self.swap_config.amount
        )

        if self.swap_config.swap_all_balance is True and self.swap_config.from_token.name.upper() == 'ETH':
            logger.error(
                "You can't use swap_all_balance = True with ETH token."
                "Using amount_from, amount_to"
            )
        if self.swap_config.swap_all_balance is True and self.swap_config.from_token.name.upper() != 'ETH':
            amount = int(balance)

        if self.swap_config.use_percentage is True:
            amount = int(balance * self.swap_config.swap_percentage)

        if amount > balance:
            logger.error(f'Not enough balance for wallet {self.wallet_address}')
            return None

        transaction = await self.get_transaction(amount)

        if not transaction:
            return False

        tx_hash = None
        confirmed = None
        while True:
            try:
                tx_hash = await self.sign_transaction(transaction)
                confirmed = await self.wait_until_tx_finished(tx_hash)
                await sleep(2)
            except Exception as ex:
                if 'nonce' in str(ex):
                    transaction.update({'nonce': await self.web3.eth.get_transaction_count(self.wallet_address)})
                    continue
                logger.error(f'Something went wrong {ex}')
                return False
            break
        if confirmed:
            logger.success(
                f'[{self.wallet_address}] | Successfully swapped {"all" if self.swap_config.swap_all_balance is True and self.swap_config.from_token.name.lower() != "eth" and self.swap_config.use_percentage is False else f"{int(self.swap_config.swap_percentage * 100)}%" if self.swap_config.use_percentage is True else self.swap_config.amount} {self.swap_config.from_token.name} tokens => {self.swap_config.to_token.name} | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}')
            return True
        else:
            raise Exception(f'[{self.wallet_address}] | Transaction failed during swap')
