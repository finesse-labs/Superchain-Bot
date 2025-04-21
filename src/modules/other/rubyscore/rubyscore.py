from asyncio import sleep
from typing import Optional

from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.models.chain import Chain
from src.utils.data.chains import chain_mapping
from src.utils.user.account import Account
from src.utils.proxy_manager import Proxy
from src.utils.common.wrappers.decorators import retry
from src.models.contracts import RubyScoreData


class RubyScore(Account):
    def __init__(self, private_key: str, chain: Chain, proxy: Optional[Proxy] = None) -> None:
        Account.__init__(self, private_key, proxy=proxy, rpc=chain.rpc)
        self.chain = chain
        self.contract_abi = RubyScoreData.abi
        self.name = 'RubyScore'

    def __str__(self) -> str:
        return f'Rubyscore voting for address [{self.wallet_address}]'

    async def _prepare_transaction(self, contract) -> Optional[dict]:
        try:
            tx = await contract.functions.vote().build_transaction({
                'value': 0,
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'from': self.wallet_address,
                'gasPrice': int(await self.web3.eth.gas_price * 1.15),
            })
            return tx
        except Exception as ex:
            logger.error(f"Failed to build transaction for RubyScore | Address: [{self.wallet_address}] | Error: {ex}")
            return None

    @retry(
        retries=RETRIES,
        delay=PAUSE_BETWEEN_RETRIES,
        backoff=1.5
    )
    async def vote(self, contract_address: str = '') -> None:
        if self.chain.chain_name == 'BASE':
            contract_address = RubyScoreData.base_address
        elif self.chain.chain_name == 'ZORA':
            contract_address = RubyScoreData.zora_address

        try:
            contract = self.load_contract(
                address=contract_address,
                web3=self.web3,
                abi=self.contract_abi
            )

            tx = await self._prepare_transaction(contract)
            if not tx:
                return

            tx_hash = await self.sign_transaction(tx)
            confirmed = await self.wait_until_tx_finished(tx_hash)

            if confirmed:
                logger.success(
                    f"Successfully voted on RubyScore for address [{self.wallet_address}]"
                    f" | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}"
                )
                await sleep(5)
        except Exception as ex:
            logger.error(f"Failed to vote on RubyScore | Address: [{self.wallet_address}] | Error: {ex}")
