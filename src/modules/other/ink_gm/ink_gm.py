from asyncio import sleep
from typing import Optional

from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.models.chain import Chain
from src.utils.data.chains import chain_mapping
from src.utils.user.account import Account
from src.utils.proxy_manager import Proxy
from src.utils.common.wrappers.decorators import retry
from src.models.contracts import InkGMData


class InkGM(Account):
    def __init__(self, private_key: str, chain: Chain, proxy: Optional[Proxy] = None) -> None:
        Account.__init__(self, private_key, proxy=proxy, rpc=chain.rpc)
        self.chain = chain
        self.contract_abi = InkGMData.abi
        self.name = 'InkGM'

    def __str__(self) -> str:
        return f'Say INK gm for [{self.wallet_address}]'

    async def _prepare_transaction(self, contract) -> Optional[dict]:
        last_block = await self.web3.eth.get_block('latest')
        max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
        base_fee = int(last_block['baseFeePerGas'] * 1.15)
        max_fee_per_gas = base_fee + max_priority_fee_per_gas
        try:
            tx = await contract.functions.gm().build_transaction({
                'value': 0,
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'from': self.wallet_address,
                "maxPriorityFeePerGas": max_priority_fee_per_gas,
                "maxFeePerGas": max_fee_per_gas
            })
            return tx
        except Exception as ex:
            if str(ex) == "('execution reverted', 'no data')":
                logger.warning(f"You have already checked in | Address: [{self.wallet_address}]")
            else:
                logger.error(f"Failed to build transaction for InkGM | Address: [{self.wallet_address}] | Error: {ex}")
            return None

    @retry(
        retries=RETRIES,
        delay=PAUSE_BETWEEN_RETRIES,
        backoff=1.5
    )
    async def vote(self) -> None:
        contract_address = InkGMData.address

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
                    f"Successfully said GM for address [{self.wallet_address}]"
                    f" | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}"
                )
                await sleep(5)
        except Exception as ex:
            logger.error(f"Failed to say GM | Address: [{self.wallet_address}] | Error: {ex}")
