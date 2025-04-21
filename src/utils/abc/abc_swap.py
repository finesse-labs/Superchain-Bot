from typing import Optional
from abc import ABC, abstractmethod
from asyncio import sleep

from eth_typing import ChecksumAddress
from web3.contract import AsyncContract
from web3.types import TxParams
from loguru import logger

from src.models.chain import Chain
from src.utils.data.chains import chain_mapping
from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account
from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.utils.common.wrappers.decorators import retry
from src.models.swap import SwapConfig
from src.utils.request_client.client import RequestClient


class ABCSwap(ABC, Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            config: SwapConfig,
            proxy: Proxy | None,
            contract_address: Optional[str],
            abi: Optional[str],
            name: str,
            chain: Chain
    ):
        self.chain = chain
        self.proxy = proxy

        Account.__init__(self, private_key, proxy=proxy, rpc=chain.rpc)
        RequestClient.__init__(self, proxy=proxy)

        self.private_key = private_key
        self.config = config
        self.contract_address = contract_address
        self.abi = abi
        self.name = name

    @abstractmethod
    async def get_amount_out(
            self, swap_config: SwapConfig, contract: AsyncContract, amount: int, from_token_address: ChecksumAddress,
            to_token_address: ChecksumAddress
    ) -> int:
        """Gets output amount"""

    @abstractmethod
    async def create_swap_tx(
            self, swap_config: SwapConfig, contract: AsyncContract, amount_out: int,
            amount: int
    ) -> tuple[TxParams, Optional[str]]:
        """Creates swap transaction"""

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def swap(self) -> Optional[bool | str]:
        contract = self.load_contract(
            self.contract_address, self.web3, self.abi
        )

        is_native = self.config.from_token.name.upper() == 'ETH'
        amount = await self.create_amount(
            is_native=is_native,
            from_token_address=self.config.from_token.address,
            web3=self.web3,
            amount=self.config.amount
        )

        balance = await self.get_wallet_balance(
            is_native=is_native,
            address=self.config.from_token.address
        )
        if balance == 0:
            logger.warning(f'[{self.wallet_address}] | {self.config.from_token.name} balance is 0')
            return 'ZeroBalance'

        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return False

        if self.config.swap_all_balance is True and self.config.from_token.name.upper() == 'ETH':
            logger.error(
                "You can't use swap_all_balance = True with ETH token."
                "Using amount_from, amount_to")
        if self.config.swap_all_balance is True and self.config.from_token.name.upper() != 'ETH':
            amount = int(balance)

        if self.config.use_percentage is True:
            amount = int(balance * self.config.swap_percentage)

        if amount > balance:
            logger.error(f'Not enough balance for wallet {self.wallet_address}')
            return None

        amount_out = await self.get_amount_out(
            self.config,
            contract,
            amount,
            self.web3.to_checksum_address(self.config.from_token.address)
            if not self.config.from_token.name.upper() == 'ETH' else None,
            self.web3.to_checksum_address(self.config.to_token.address)
            if not self.config.to_token.name.upper() == 'ETH' else None,
        )

        transaction, to = None, None
        try:
            transaction, to = await self.create_swap_tx(
                self.config,
                contract,
                amount_out,
                amount
            )
            if to and self.config.from_token.name != 'ETH':
                await self.approve_token(
                    amount,
                    self.private_key,
                    self.config.from_token.address,
                    to,
                    self.wallet_address,
                    self.web3
                )
                await sleep(3)
            gas = await self.web3.eth.estimate_gas(transaction)
            transaction.update({'gas': int(gas)})
        except Exception as ex:
            if 'execution reverted' in str(ex):
                logger.error(f'[{self.wallet_address}] | Failed to get transaction')
                return False
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
                f'[{self.wallet_address}] | Successfully swapped {"all" if self.config.swap_all_balance is True and self.config.from_token.name.lower() != "eth" and self.config.use_percentage is False else f"{int(self.config.swap_percentage * 100)}%" if self.config.use_percentage is True else self.config.amount} {self.config.from_token.name} tokens => {self.config.to_token.name} | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}')
            return True
        else:
            raise Exception(f'[{self.wallet_address}] | Transaction failed during swap')
