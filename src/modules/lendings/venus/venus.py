import random
from asyncio import sleep
from typing import Optional

from loguru import logger

from config import PAUSE_BETWEEN_RETRIES, RETRIES, PAUSE_BETWEEN_MODULES
from src.models.contracts import VenusData
from src.utils.common.wrappers.decorators import retry
from src.utils.data.chains import chain_mapping
from src.models.chain import Chain
from src.utils.data.tokens import tokens
from src.utils.proxy_manager import Proxy
from src.utils.request_client.curl_cffi_client import CurlCffiClient
from src.utils.user.account import Account


class Venus(Account, CurlCffiClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            action: str,
            chain: Chain
    ):
        self.chain = chain
        self.action = action
        Account.__init__(self, private_key=private_key, proxy=proxy, rpc=chain.rpc)
        CurlCffiClient.__init__(self, proxy=proxy)

    def __str__(self) -> str:
        if self.action == 'deposit':
            return f'[{self.wallet_address}] | Depositing to Venus...'
        else:
            return f'[{self.wallet_address}] | Withdrawing from Venus...'

    async def get_all_pools(self):
        response_json, status = await self.make_request(
            method="GET",
            url=f'https://api.venus.io/pools?chainId={self.chain.chain_id}',
        )
        if status == 200:
            return response_json['result'][0]['markets']

    async def get_pool_address(self, token: str) -> Optional[str]:
        all_pools = await self.get_all_pools()
        for pool in all_pools:
            if token in pool['symbol']:
                return pool['address']

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def deposit_in_pool(self, token: str, deposit_percentage: float) -> Optional[bool]:
        token_address = tokens['UNICHAIN'][token]

        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return None

        token_balance = await self.get_wallet_balance(is_native=False, address=token_address)
        if token_balance == 0:
            logger.error(f'[{self.wallet_address}] | {token} balance is 0')
            return None

        amount = int(token_balance * deposit_percentage)
        if amount > token_balance:
            logger.error(f'[{self.wallet_address}] | Not enough {token} balance.')
            return None

        pool_address = await self.get_pool_address(token)
        await self.approve_token(
            amount,
            self.private_key,
            token_address,
            pool_address,
            self.wallet_address,
            self.web3
        )
        await sleep(3)

        contract = self.load_contract(
            address=pool_address,
            web3=self.web3,
            abi=VenusData.abi
        )

        last_block = await self.web3.eth.get_block('latest')
        max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
        base_fee = int(last_block['baseFeePerGas'] * 1.15)
        max_fee_per_gas = base_fee + max_priority_fee_per_gas

        transaction = await contract.functions.mint(
            amount
        ).build_transaction({
            'value': 0,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'maxFeePerGas': max_fee_per_gas,
        })

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
                f'[{self.wallet_address}] | Successfully deposited {round(deposit_percentage * 100, 2)}% of {token} token into Venus pool | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}')
            return True
        else:
            raise Exception(f'[{self.wallet_address}] | Transaction failed during deposit')

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def withdraw_all(self) -> Optional[bool]:
        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return None

        pools = await self.get_all_pools()

        pool_mapping = {}
        for pool in pools:
            pool_mapping[pool['symbol']] = pool['address']

        for token_name, address in pool_mapping.items():
            lp_balance = await self.get_wallet_balance(is_native=False, address=address)
            if lp_balance == 0:
                logger.warning(f'[{self.wallet_address}] | {token_name} balance is 0. Nothing to withdraw...')
                await sleep(0.1)
                continue

            contract = self.load_contract(
                address=address,
                web3=self.web3,
                abi=VenusData.abi
            )

            last_block = await self.web3.eth.get_block('latest')
            max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
            base_fee = int(last_block['baseFeePerGas'] * 1.15)
            max_fee_per_gas = base_fee + max_priority_fee_per_gas

            transaction = await contract.functions.redeem(
                lp_balance
            ).build_transaction({
                'value': 0,
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'from': self.wallet_address,
                'maxPriorityFeePerGas': max_priority_fee_per_gas,
                'maxFeePerGas': max_fee_per_gas,
            })

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
                break
            if confirmed:
                logger.success(
                    f'[{self.wallet_address}] | Successfully withdrawn {token_name} from Venus pool | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}')
                time_to_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1])
                logger.info(f'Sleeping {time_to_sleep} seconds...')
                await sleep(time_to_sleep)
            else:
                raise Exception(f'[{self.wallet_address}] | Transaction failed during withdrawal')

        return True