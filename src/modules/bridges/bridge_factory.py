from typing import Callable, Optional

from web3.contract import AsyncContract
from web3.types import TxParams

from src.modules.bridges.across.across_transactions import create_across_tx
from src.modules.bridges.relay.relay_transaction import create_relay_tx
from src.modules.bridges.super_bridge.super_bridge_transaction import create_super_bridge_tx
from src.utils.abc.abc_bridge import ABCBridge
from src.models.bridge import BridgeConfig
from src.models.contracts import *
from src.utils.proxy_manager import Proxy


def create_bridge_class(
        class_name: str,
        contract_data,
        name: str,
        bridge_tx_function: Callable
) -> type[ABCBridge]:
    class BridgeClass(ABCBridge):
        def __init__(
                self,
                private_key: str,
                bridge_config: BridgeConfig,
                proxy: Proxy | None
        ):
            contract_address = contract_data.address
            abi = contract_data.abi

            super().__init__(
                private_key=private_key,
                proxy=proxy,
                bridge_config=bridge_config,
                contract_address=contract_address,
                abi=abi,
                name=name
            )

        def __str__(self) -> str:
            return (f'{self.__class__.__name__} | [{self.wallet_address}] | '
                    f'[{self.config.from_chain.chain_name} => {self.config.to_chain.chain_name}]')

        async def create_bridge_transaction(
                self, contract: Optional[AsyncContract], bridge_config: BridgeConfig, amount: int
        ) -> TxParams:
            return await bridge_tx_function(self, contract, bridge_config, amount)

    BridgeClass.__name__ = class_name
    return BridgeClass


SuperBridge = create_bridge_class(
    class_name='SuperBridge',
    contract_data=SuperBridgeData,
    name='SuperBridge',
    bridge_tx_function=create_super_bridge_tx
)

AcrossBridge = create_bridge_class(
    class_name='AcrossBridge',
    contract_data=AcrossBridgeData,
    name='Across',
    bridge_tx_function=create_across_tx
)

RelayBridge = create_bridge_class(
    class_name='RelayBridge',
    contract_data=RelayData,
    name='Relay',
    bridge_tx_function=create_relay_tx
)