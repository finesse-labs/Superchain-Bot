from typing import (
    Awaitable,
    Callable,
    Optional,
    Union,
)

from asyncio import sleep

from web3.contract import AsyncContract
from web3 import AsyncWeb3
from loguru import logger
from src.models.contracts import ERC20

from eth_typing import (
    Address,
    HexStr, ChecksumAddress,
)


class Utils:
    @staticmethod
    def load_contract(address: str, web3: AsyncWeb3, abi: str) -> Optional[AsyncContract]:
        if address is None:
            return None

        address = web3.to_checksum_address(address)
        return web3.eth.contract(address=address, abi=abi)

    async def get_decimals(self, contract_address: str, web3: AsyncWeb3) -> int:
        contract = self.load_contract(contract_address, web3, ERC20.abi)
        decimals = await contract.functions.decimals().call()
        return decimals

    async def approve_token(
            self,
            amount: int,
            private_key: str,
            from_token_address: str,
            spender: str,
            address_wallet: Address | ChecksumAddress,
            web3: AsyncWeb3
    ) -> Optional[HexStr]:
        while True:
            try:
                spender = web3.to_checksum_address(spender)
                contract = self.load_contract(from_token_address, web3, ERC20.abi)
                allowance_amount = await self.check_allowance(web3, from_token_address, address_wallet, spender)
                if amount > allowance_amount:
                    logger.debug('🛠️ | Approving token...')
                    tx = await contract.functions.approve(
                        spender,
                        int(2 ** 256 - 1)
                    ).build_transaction({
                        'chainId': await web3.eth.chain_id,
                        'from': address_wallet,
                        'nonce': await web3.eth.get_transaction_count(address_wallet),
                        'gasPrice': await web3.eth.gas_price
                    })

                    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
                    raw_tx_hash = await web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    await sleep(10)
                    tx_receipt = await web3.eth.wait_for_transaction_receipt(raw_tx_hash)
                    while tx_receipt is None:
                        await sleep(1)
                        tx_receipt = await web3.eth.get_transaction_receipt(raw_tx_hash)
                    tx_hash = web3.to_hex(raw_tx_hash)
                    logger.success(f'✔️ | Token approved')
                    await sleep(5)
                    return tx_hash
                else:
                    break
            except ValueError as ex:
                if 'max fee per gas less than block base fee' in str(ex):
                    await sleep(1)
                    continue

            except Exception as ex:
                logger.error(f'Something went wrong | {ex}')
                break

    @staticmethod
    async def check_allowance(
            web3: AsyncWeb3,
            from_token_address: str,
            address_wallet: Address,
            spender: str
    ) -> Optional[int]:
        try:
            contract = web3.eth.contract(address=web3.to_checksum_address(from_token_address),
                                         abi=ERC20.abi)
            amount_approved = await contract.functions.allowance(address_wallet, spender).call()
            return amount_approved

        except Exception as ex:
            logger.error(f'Something went wrong | {ex}')

    async def setup_decimals(
            self, is_native: bool, from_token_address: str, web3: AsyncWeb3
    ) -> Union[int, Callable[[str, AsyncWeb3], Awaitable[int]]]:
        if is_native:
            return 18
        else:
            return await self.get_decimals(from_token_address, web3)

    async def create_amount(
            self, is_native: bool, from_token_address: str, web3: AsyncWeb3, amount: float
    ) -> int:
        decimals = await self.setup_decimals(is_native, from_token_address, web3)
        amount = int(amount * 10 ** decimals)
        return amount
