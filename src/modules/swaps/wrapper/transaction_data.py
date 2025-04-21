from eth_typing import Address
from web3.types import TxParams
from web3 import AsyncWeb3

from src.models.contracts import WrapData
from src.utils.data.tokens import tokens


async def create_wrap_tx(
        self,
        wallet_address: Address,
        from_token: str,
        web3: AsyncWeb3,
        amount: int
) -> TxParams:
    contract = web3.eth.contract(address=tokens[self.chain.chain_name]['WETH'], abi=WrapData.abi)
    if from_token.upper() == 'ETH':
        tx = await contract.functions.deposit().build_transaction({
            'value': amount,
            'nonce': await web3.eth.get_transaction_count(wallet_address),
            'from': wallet_address,
            'gasPrice': int(await web3.eth.gas_price * 1.15)
        })
    else:
        tx = await contract.functions.withdraw(amount).build_transaction({
            'value': 0,
            'nonce': await web3.eth.get_transaction_count(wallet_address),
            'from': wallet_address,
            'gasPrice': int(await web3.eth.gas_price * 1.15)
        })
    return tx
