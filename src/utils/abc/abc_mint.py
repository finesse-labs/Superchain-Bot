from abc import ABC, abstractmethod
from asyncio import sleep
from typing import Optional

from aiohttp import ClientSession
from web3.contract import Contract
from web3.types import TxParams
from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account
from src.utils.common.wrappers.decorators import retry


class ABCMint(ABC, Account):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            contract_address: str,
            abi: str,
            name: str,

    ):
        super().__init__(private_key=private_key, proxy=proxy)
        self.contract_address = contract_address
        self.abi = abi
        self.name = name

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def mint(self) -> Optional[bool | str]:
        balance = await self.get_wallet_balance(is_native=True)
        if balance == 0:
            logger.error(f'Your MON balance is 0 | [{self.wallet_address}]')
            return None

        contract = self.load_contract(
            address=self.contract_address,
            web3=self.web3,
            abi=self.abi
        )

        tx = await self.create_mint_tx(contract)

        if tx is None:
            return None

        try:
            tx_hash = await self.sign_transaction(tx)
            confirmed = await self.wait_until_tx_finished(tx_hash)
        except Exception as ex:
            logger.error(f'Something went wrong {ex}')
            return False

        if confirmed:
            logger.success(
                f'Successfully minted {self.name} NFT | TX: https://testnet.monadexplorer.com/tx/{tx_hash}'
            )
            return True
        else:
            raise Exception(f'[{self.wallet_address}] | Transaction failed during mint')

    @abstractmethod
    async def create_mint_tx(self, contract) -> None:
        """Creates mint transaction"""
