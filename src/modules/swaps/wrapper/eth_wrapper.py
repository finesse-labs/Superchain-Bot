from typing import Union, List, Optional
import random

from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.models.chain import Chain
from src.modules.swaps.wrapper.transaction_data import create_wrap_tx
from src.utils.common.exceptions import TransactionFailedError
from src.utils.common.wrappers.decorators import retry
from src.utils.data.chains import chain_mapping
from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account
from src.utils.data.tokens import tokens


class Wrapper(Account):
    def __init__(
            self,
            private_key: str,
            amount: Union[float, List[float]],
            use_all_balance: bool,
            use_percentage: bool,
            percentage_to_wrap: Union[float, List[float]],
            proxy: Proxy | None,
            chain: Chain
    ):

        super().__init__(private_key=private_key, proxy=proxy, rpc=chain.rpc)
        self.chain = chain
        if isinstance(amount, List):
            self.amount = round(random.uniform(amount[0], amount[1]), 7)
        elif isinstance(amount, (float, int)):
            self.amount = amount
        else:
            logger.error(f'amount must be List[float] of float. Got {type(amount)}')
            return

        self.use_all_balance = use_all_balance
        self.use_percentage = use_percentage

        if isinstance(percentage_to_wrap, List):
            self.percentage_to_wrap = random.uniform(percentage_to_wrap[0], percentage_to_wrap[1])
        elif isinstance(percentage_to_wrap, float):
            self.percentage_to_wrap = percentage_to_wrap
        else:
            logger.error(f'percentage_to_wrap must be List[float] or float. Got {type(percentage_to_wrap)}')
            return

    def __repr__(self) -> str:
        return f'[{self.wallet_address}] | [{self.chain.chain_name}] | Wrapper'

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def wrap(self, action: str) -> Optional[bool]:
        if action.upper() == 'WRAP':
            token = 'ETH'
        else:
            token = 'WETH'
        is_native = action.upper() == 'WRAP'
        balance = await self.get_wallet_balance(
            is_native=is_native,
            address=tokens[self.chain.chain_name]['WETH']
        )

        if balance == 0:
            logger.warning(f"[{self.wallet_address}] | WETH balance is 0")
            return None

        amount = int(self.amount * 10 ** 18)

        if self.use_all_balance is True:
            if action.upper() == 'UNWRAP':
                amount = balance
            elif action.upper() == 'WRAP':
                amount = int(balance * self.percentage_to_wrap)

        if self.use_percentage is True:
            if action.upper() == 'UNWRAP':
                amount = balance
            elif action.upper() == 'WRAP':
                amount = int(balance * self.percentage_to_wrap)

        tx = await create_wrap_tx(self, self.wallet_address, token, self.web3, amount)

        tx_hash = await self.sign_transaction(tx)
        confirmed = await self.wait_until_tx_finished(tx_hash)

        if confirmed:
            logger.success(
                f'Successfully {"unwrapped" if action.lower() == "unwrap" else "wrapped"} {amount / 10 ** 18} {"WETH => ETH" if action.lower() == "unwrap" else "ETH => WETH"} | TX: {chain_mapping[self.chain.chain_name].scan}/{tx_hash}'
            )
        else:
            raise TransactionFailedError(f"Transaction failed for TX: {tx_hash}")
