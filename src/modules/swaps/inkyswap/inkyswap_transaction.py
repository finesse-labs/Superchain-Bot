from time import time

from web3.contract import AsyncContract
from web3.types import TxParams
from eth_typing import Address

from config import SLIPPAGE
from src.models.swap import SwapConfig
from src.utils.data.tokens import tokens


async def get_amount_out_inky(
        swap_config: SwapConfig, contract: AsyncContract, amount: int, from_token_address: Address,
        to_token_address: Address
) -> int:
    if swap_config.from_token.name.upper() == 'ETH':
        from_token_address = tokens['INK']['WETH']
    else:
        to_token_address = tokens['INK']['WETH']
    amount_out = await contract.functions.getAmountsOut(
        amount,
        [from_token_address, to_token_address]
    ).call()
    return amount_out[1]


async def create_inky_swap_tx(
        self,
        swap_config: SwapConfig,
        contract: AsyncContract,
        amount_out: int,
        amount: int,
) -> tuple[TxParams, str]:
    last_block = await self.web3.eth.get_block('latest')
    max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
    base_fee = int(last_block['baseFeePerGas'] * 1.15)
    max_fee_per_gas = base_fee + max_priority_fee_per_gas

    if swap_config.from_token.name.upper() == 'ETH':
        from_token_address = tokens['INK']['WETH']

        tx = await contract.functions.swapExactETHForTokens(
            int(amount_out * (1 - SLIPPAGE)),
            [self.web3.to_checksum_address(from_token_address),
             self.web3.to_checksum_address(swap_config.to_token.address)],
            self.wallet_address,
            int(time() + 1200)
        ).build_transaction({
            'value': amount if swap_config.from_token.name.upper() == 'ETH' else 0,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'maxFeePerGas': max_fee_per_gas,
        })
    else:
        to_token_address = tokens['INK']['WETH']

        tx = await contract.functions.swapExactTokensForETH(
            amount,
            int(amount_out * (1 - SLIPPAGE)),
            [self.web3.to_checksum_address(swap_config.from_token.address),
             to_token_address],
            self.wallet_address,
            int(time() + 1200)
        ).build_transaction({
            'value': amount if swap_config.from_token.name.upper() == 'ETH' else 0,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'maxFeePerGas': max_fee_per_gas,
        })
    return tx, None
