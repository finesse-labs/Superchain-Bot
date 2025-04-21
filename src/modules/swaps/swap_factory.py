from typing import Callable, Optional

from eth_typing import ChecksumAddress
from web3.contract import AsyncContract
from web3.types import TxParams

from src.models.chain import Chain
from src.models.contracts import *
from src.modules.swaps.bungee.bungee_transaction import create_bungee_swap_tx
from src.modules.swaps.defillama.defillama_transaction import create_defillama_swap_tx
from src.modules.swaps.inkyswap.inkyswap_transaction import create_inky_swap_tx, get_amount_out_inky

from src.modules.swaps.matcha.matcha_transaction import create_matcha_swap_tx
from src.modules.swaps.oku_swap.oku_transaction import create_oku_swap_tx
from src.modules.swaps.owlto.owlto_transaction import create_owlto_swap_tx
from src.modules.swaps.relayswap.relay_transaction import create_relay_swap_tx
from src.modules.swaps.sushiswap.sushiswap_transaction import create_sushiswap_swap_tx
from src.utils.abc.abc_swap import ABCSwap
from src.utils.proxy_manager import Proxy
from src.models.swap import (
    Token,
    SwapConfig
)


def create_swap_class(
        class_name: str,
        contract_data,
        name: str,
        swap_tx_function: Callable,
        amount_out_function: Optional[Callable]
) -> type[ABCSwap]:
    class SwapClass(ABCSwap):
        def __init__(
                self,
                private_key: str,
                *,
                from_token: str | list[str],
                to_token: str | list[str],
                amount: float | list[float],
                use_percentage: bool,
                swap_percentage: float | list[float],
                swap_all_balance: bool,
                proxy: Proxy | None,
                chain: Chain
        ):
            contract_address = contract_data.address
            abi = contract_data.abi
            swap_config = SwapConfig(
                from_token=Token(
                    chain_name=chain.chain_name,
                    name=from_token

                ),
                to_token=Token(
                    chain_name=chain.chain_name,
                    name=to_token
                ),
                amount=amount,
                use_percentage=use_percentage,
                swap_percentage=swap_percentage,
                swap_all_balance=swap_all_balance,
            )
            super().__init__(
                private_key=private_key,
                config=swap_config,
                proxy=proxy,
                contract_address=contract_address,
                abi=abi,
                name=name,
                chain=chain
            )

        def __str__(self) -> str:
            return f'{self.__class__.__name__} | [{self.wallet_address}] | [{self.chain.chain_name}] |' \
                   f' [{self.config.from_token.name} => {self.config.to_token.name}]'

        async def get_amount_out(
                self,
                swap_config: SwapConfig,
                contract: AsyncContract,
                amount: int,
                from_token_address: ChecksumAddress,
                to_token_address: ChecksumAddress
        ) -> Optional[int]:
            if amount_out_function:
                return await amount_out_function(swap_config, contract, amount, from_token_address, to_token_address)

        async def create_swap_tx(
                self,
                swap_config: SwapConfig,
                contract: AsyncContract,
                amount_out: int,
                amount: int
        ) -> tuple[TxParams, Optional[str]]:
            return await swap_tx_function(self, swap_config, contract, amount_out, amount)

    SwapClass.__name__ = class_name
    return SwapClass


MatchaSwap = create_swap_class(
    class_name='MatchaSwap',
    contract_data=MatchaSwapData,
    name='Matcha',
    swap_tx_function=create_matcha_swap_tx,
    amount_out_function=None
)

BungeeSwap = create_swap_class(
    class_name='BungeeSwap',
    contract_data=BungeeSwapData,
    name='Bungee',
    swap_tx_function=create_bungee_swap_tx,
    amount_out_function=None
)

SushiSwap = create_swap_class(
    class_name='SushiswapSwap',
    contract_data=SushiswapData,
    name='Sushiswap',
    swap_tx_function=create_sushiswap_swap_tx,
    amount_out_function=None
)

OwltoSwap = create_swap_class(
    class_name='OwltoSwap',
    contract_data=OwltoData,
    name='Owlto',
    swap_tx_function=create_owlto_swap_tx,
    amount_out_function=None
)

RelaySwap = create_swap_class(
    class_name='RelaySwap',
    contract_data=RelayData,
    name='Relay',
    swap_tx_function=create_relay_swap_tx,
    amount_out_function=None
)

InkySwap = create_swap_class(
    class_name='InkySwap',
    contract_data=InkySwapData,
    name='Inky',
    swap_tx_function=create_inky_swap_tx,
    amount_out_function=get_amount_out_inky
)

OkuSwap = create_swap_class(
    class_name='OkuSwap',
    contract_data=OkuData,
    name='Oku',
    swap_tx_function=create_oku_swap_tx,
    amount_out_function=None
)

DefillamaSwap = create_swap_class(
    class_name='DefillamaSwap',
    contract_data=DefillamaData,
    name='Defillama',
    swap_tx_function=create_defillama_swap_tx,
    amount_out_function=None
)
