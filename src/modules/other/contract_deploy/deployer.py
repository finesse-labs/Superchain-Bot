from asyncio import sleep
from typing import Optional

from loguru import logger

from config import PAUSE_BETWEEN_RETRIES, RETRIES
from src.models.chain import Chain
from src.utils.data.chains import chain_mapping
from src.utils.user.account import Account
from src.utils.proxy_manager import Proxy
from src.utils.common.wrappers.decorators import retry
from src.models.contracts import DeployData


class Deployer(Account):
    def __init__(self, private_key: str, chain: Chain, proxy: Optional[Proxy] = None) -> None:
        Account.__init__(self, private_key, proxy=proxy, rpc=chain.rpc)
        self.chain = chain
        self.contract_abi = DeployData.abi

    def __str__(self) -> str:
        return f'Deploying contract for address [{self.wallet_address}]'

    async def _prepare_deploy_transaction(self) -> dict:
        try:
            contract = self.web3.eth.contract(
                abi=self.contract_abi,
                bytecode='0x'
            )
            constructor = contract.constructor()

            tx = await constructor.build_transaction({
                'value': 0,
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'from': self.wallet_address,
                'gasPrice': int(await self.web3.eth.gas_price * 1.15),
            })

            gas_limit = await self.web3.eth.estimate_gas(tx)
            tx.update({'gas': gas_limit})

            return tx
        except Exception as ex:
            logger.error(f"Failed to prepare deploy transaction | Address: [{self.wallet_address}] | Error: {ex}")
            return {}

    @retry(
        retries=RETRIES,
        delay=PAUSE_BETWEEN_RETRIES,
        backoff=1.5
    )
    async def deploy(self) -> None:
        try:
            tx = await self._prepare_deploy_transaction()
            if not tx:
                return

            tx_hash = await self.sign_transaction(tx)
            confirmed = await self.wait_until_tx_finished(tx_hash)

            if confirmed:
                logger.success(
                    f"Successfully deployed contract for address [{self.wallet_address}]"
                    f" | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}"
                )
                await sleep(5)
        except Exception as ex:
            logger.error(f"Failed to deploy contract | Address: [{self.wallet_address}] | Error: {ex}")
