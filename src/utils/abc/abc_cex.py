from abc import ABC, abstractmethod
from asyncio import sleep
import random
from typing import Callable, Optional

import ccxt
from loguru import logger
from web3.contract import AsyncContract

from config import RETRIES, PAUSE_BETWEEN_RETRIES, OKXWithdrawSettings
from src.models.cex import CEXConfig
from src.models.contracts import ERC20
from src.utils.data.chains import chain_mapping
from src.utils.data.tokens import tokens
from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account
from src.utils.common.wrappers.decorators import retry


class CEX(ABC, Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            config: CEXConfig
    ):
        self.amount = None
        self.token = None
        self.chain: Optional[str] = None
        self.to_address = None
        self.keep_balance = None
        self.api_key = None
        self.api_secret = None
        self.passphrase = None
        self.password = None
        self.proxy = None
        self.exchange_instance = None

        self.config = config
        if config.okx_config:
            self.setup_exchange(exchange_config=config.okx_config, exchange_type='okx')
        elif config.binance_config:
            self.setup_exchange(exchange_config=config.binance_config, exchange_type='binance')
        elif config.bitget_config:
            self.setup_exchange(exchange_config=config.bitget_config, exchange_type='bitget')
        if isinstance(self.chain, list):
            self.chain = random.choice(self.chain)

        rpc = chain_mapping[self.chain.upper()].rpc
        Account.__init__(self, private_key=private_key, proxy=proxy, rpc=rpc)
        RequestClient.__init__(self, proxy=self.proxy)

    @abstractmethod
    def call_withdraw(self, exchange_instance) -> Optional[bool]:
        """Calls withdraw function"""

    @abstractmethod
    async def call_sub_transfer(
            self, token: str, api_key: str, api_secret: str, api_passphrase: Optional[str],
            api_password: Optional[str], request_func: Callable
    ):
        """Calls transfer from sub-account to main-account"""

    async def withdraw(self) -> Optional[bool]:
        all_chains = OKXWithdrawSettings.chain
        if isinstance(all_chains, str):
            all_chains = [all_chains]
        chain = await self.check_available_chains(chains=all_chains)
        if chain:
            return True

        balance_before_withdraw, token_contract = await self.get_balance_before_withdrawal()

        logger.debug(f'Checking sub-accounts balances before withdrawal...')
        await self.call_sub_transfer(
            token=self.token,
            api_key=self.api_key,
            api_secret=self.api_secret,
            api_passphrase=self.passphrase,
            api_password=self.password,
            request_func=self.make_request
        )
        await sleep(10)
        withdrawn = self.call_withdraw(self.exchange_instance)
        if withdrawn:
            await self.wait_for_withdrawal(balance_before_withdraw, token_contract)
            return True

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def deposit(self) -> Optional[bool]:
        is_native = self.token.upper() == 'ETH'
        balance = await self.get_wallet_balance(
            is_native=is_native, address=tokens[self.chain.upper()][self.token.upper()]
        )
        if balance == 0:
            logger.error(f'Your balance is 0 | {self.wallet_address}')
            return True

        decimals = 18
        if not is_native:
            token_contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(tokens[self.token.upper()]),
                abi=ERC20.abi
            )
            decimals = await token_contract.functions.decimals().call()

        amount = int(balance - self.keep_balance * 10 ** decimals)

        if self.token.upper() != 'ETH':
            token_contract = self.load_contract(
                address=tokens[self.token.upper()],
                web3=self.web3,
                abi=ERC20.abi
            )

            tx = await token_contract.functions.transfer(
                self.web3.to_checksum_address(self.to_address),
                amount
            ).build_transaction({
                'value': 0,
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'from': self.wallet_address,
                'gasPrice': int(await self.web3.eth.gas_price * 1.15)
            })
        else:
            tx = {
                'from': self.wallet_address,
                'value': amount,
                'to': self.web3.to_checksum_address(self.to_address),
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'chainId': await self.web3.eth.chain_id,
                'gasPrice': int(await self.web3.eth.gas_price * 1.15)
            }

        if self.keep_balance == 0:
            tx['value'] = 0
            gas_limit = await self.web3.eth.estimate_gas(tx)
            tx.update({'value': int(balance - (gas_limit * await self.web3.eth.gas_price * 1.5))})

        gas_limit = await self.web3.eth.estimate_gas(tx)
        tx.update({'gas': gas_limit})

        tx_hash = await self.sign_transaction(tx)
        confirmed = await self.wait_until_tx_finished(tx_hash)
        if confirmed:
            logger.success(
                f'Successfully withdrawn {round((amount / 10 ** decimals), 3)} {self.token} '
                f'from {self.wallet_address} to '
                f'{self.to_address} TX: {chain_mapping[self.chain.upper()].scan}/{tx_hash}'
            )
            return True
        else:
            raise Exception(f'[{self.wallet_address}] | Transaction failed during transfer')

    async def wait_for_withdrawal(
            self, balance_before_withdraw: int, token_contract: AsyncContract | None = None
    ) -> None:
        logger.info(f'Waiting for {self.token} to arrive...')
        while True:
            try:
                if token_contract:
                    balance = await token_contract.functions.balanceOf(self.to_address).call()
                else:
                    balance = await self.web3.eth.get_balance(self.web3.to_checksum_address(self.to_address))
                if balance > balance_before_withdraw:
                    logger.success(f'{self.token} has arrived | [{self.to_address}]')
                    break
                await sleep(20)
            except Exception as ex:
                logger.error(f'Something went wrong {ex}')
                await sleep(10)
                continue

    async def get_balance_before_withdrawal(self) -> tuple[int, AsyncContract | None]:
        is_native = self.token.upper() == 'ETH'
        if not is_native:
            contract = self.load_contract(
                address=tokens[self.chain.upper()][self.token.upper()],
                web3=self.web3,
                abi=ERC20.abi
            )
            balance = await contract.functions.balanceOf(self.to_address).call()
            return balance, contract

        balance = await self.web3.eth.get_balance(self.web3.to_checksum_address(self.to_address))
        return balance, None

    def setup_exchange(self, exchange_config, exchange_type):
        if exchange_config.withdraw_settings:
            self.amount = exchange_config.withdraw_settings.calculated_amount
            self.token = exchange_config.withdraw_settings.token
            self.chain = exchange_config.withdraw_settings.chain
            self.to_address = exchange_config.withdraw_settings.to_address

        self.api_key = exchange_config.API_KEY
        self.api_secret = exchange_config.API_SECRET
        self.proxy = exchange_config.PROXY

        if exchange_type == 'okx':
            self.passphrase = exchange_config.PASSPHRASE
            self.exchange_instance = ccxt.okx({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'password': self.passphrase,
                'enableRateLimit': True,
                'proxies': self.get_proxies(self.proxy)
            })
        elif exchange_type == 'binance':
            self.exchange_instance = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'proxies': self.get_proxies(self.proxy),
                'options': {'defaultType': 'spot'}
            })
        elif exchange_type == 'bitget':
            self.password = exchange_config.PASSWORD
            self.exchange_instance = ccxt.bitget({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'password': self.password,
                'enableRateLimit': True,
                'proxies': self.get_proxies(self.proxy),
                'options': {'defaultType': 'spot'}
            })

        if exchange_config.deposit_settings:
            self.token = exchange_config.deposit_settings.token
            self.chain = exchange_config.deposit_settings.chain
            self.to_address = exchange_config.deposit_settings.to_address
            self.keep_balance = exchange_config.deposit_settings.calculated_keep_balance

    @staticmethod
    def get_proxies(proxy: str | None) -> dict[str, str | None]:
        return {
            'http': proxy if proxy else None,
            'https': proxy if proxy else None
        }

    async def check_available_chains(self, chains: list[str]) -> Optional[str]:
        for chain in chains:
            rpc = chain_mapping[chain.upper()].rpc
            account = Account(self.private_key, proxy=self.proxy, rpc=rpc)
            balance = await account.get_wallet_balance(is_native=True)
            if balance >= OKXWithdrawSettings.min_eth_balance * 10 ** 18:
                logger.debug(
                    f'[{self.wallet_address}] '
                    f'| В сети {chain} уже есть необходимый баланс. Вывод не требуется.'
                )
                return chain
