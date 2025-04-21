import asyncio
import copy
import random
import traceback
import aiohttp.client_exceptions
import python_socks

from src.modules import Logger, RequestClient, Client
from config import AMOUNT_PERCENT_WRAPS
from src.modules.interfaces import SoftwareException, SoftwareExceptionWithoutRetry, CriticalException, \
    SoftwareExceptionHandled
from src.utils.tools import helper, gas_checker, sleep_tools
from config import (
    TOKENS_PER_CHAIN, OMNICHAIN_WRAPED_NETWORKS, OMNICHAIN_NETWORKS_DATA,
    TOKENS_PER_CHAIN2, CHAIN_NAME,
    COINGECKO_TOKEN_API_NAMES
)
from config import (
    STARGATE_CHAINS, STARGATE_TOKENS,
    L0_SEARCH_DATA, L0_BRIDGE_COUNT, STARGATE_AMOUNT
)


class Custom(Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    async def collect_eth_util(self):
        from functions import (
            swap_odos, swap_oneinch, swap_izumi, swap_syncswap, swap_bladeswap, unwrap_eth, swap_ambient
        )

        self.logger_msg(*self.client.acc_info, msg=f"Started collecting tokens in ETH")

        func = {
            'Arbitrum': [swap_odos, swap_oneinch],
            'Optimism': [swap_odos, swap_oneinch],
            'Base': [swap_izumi, swap_odos, swap_oneinch],
            'Blast': [swap_bladeswap],
            'Linea': [swap_izumi, swap_syncswap],
            'Scroll': [swap_izumi, swap_ambient],
            'zkSync': [swap_izumi, swap_syncswap, swap_oneinch]
        }[self.client.network.name]

        wallet_balance = {k: await self.client.get_token_balance(k, False)
                          for k, v in TOKENS_PER_CHAIN[self.client.network.name].items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = await self.client.get_token_price('ethereum')

        for token in ['ETH', 'WETH']:
            if token in valid_wallet_balance:
                valid_wallet_balance[token] *= eth_price

        if valid_wallet_balance['ETH'] < 0.5:
            self.logger_msg(*self.client.acc_info, msg=f'Account has not enough ETH for swap fee', type_msg='warning')
            return True

        if len(valid_wallet_balance.values()) > 1:
            try:
                for token_name, token_balance in valid_wallet_balance.items():
                    if token_name != 'ETH':
                        amount_in_wei = wallet_balance[token_name][0]
                        amount = float(f"{(amount_in_wei / 10 ** await self.client.get_decimals(token_name)):.6f}")
                        amount_in_usd = valid_wallet_balance[token_name]
                        if amount_in_usd > 1:
                            from_token_name, to_token_name = token_name, 'ETH'
                            data = from_token_name, to_token_name, amount, amount_in_wei
                            counter = 0
                            while True:
                                result = False
                                if from_token_name == 'WETH':
                                    module_func = unwrap_eth
                                    data = amount_in_wei
                                else:
                                    module_func = random.choice(func)
                                try:
                                    self.logger_msg(
                                        *self.client.acc_info, msg=f'Launching swap module', type_msg='warning'
                                    )
                                    result = await module_func(
                                        self.client.account_name, self.client.private_key, self.client.network,
                                        self.client.proxy_init, swapdata=data
                                    )
                                    if not result:
                                        counter += 1
                                except Exception as error:
                                    self.logger_msg(
                                        *self.client.acc_info, msg=f'Error in collector: {error}', type_msg='warning'
                                    )
                                    counter += 1
                                    pass
                                if result or counter == 3:
                                    break
                        else:
                            self.logger_msg(*self.client.acc_info, msg=f"{token_name} balance < 1$")
                    await sleep_tools(self, 10, 50)
            except Exception as error:
                self.logger_msg(*self.client.acc_info, msg=f"Error in collector route. Error: {error}")
        else:
            self.logger_msg(*self.client.acc_info, msg=f"Account balance already in ETH!", type_msg='warning')

    @helper
    async def collect_eth(self):
        await self.collect_eth_util()

        return True

    @helper
    async def wraps_abuser(self):
        from functions import swap_odos, swap_oneinch, swap_xyfinance

        func = {
            'Base': [swap_odos, swap_oneinch],
            'Linea': [swap_xyfinance],
            'Scroll': [swap_xyfinance],
            'zkSync': [swap_odos, swap_oneinch]
        }[self.client.network.name]

        current_tokens = list(TOKENS_PER_CHAIN[self.client.network.name].items())[:2]

        wrapper_counter = 0
        for _ in range(2):
            wallet_balance = {k: await self.client.get_token_balance(k, False) for k, v in current_tokens}
            valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
            eth_price = await self.client.get_token_price('ethereum')

            if 'ETH' in valid_wallet_balance:
                valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

            if 'WETH' in valid_wallet_balance:
                valid_wallet_balance['WETH'] = valid_wallet_balance['WETH'] * eth_price

            max_token = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])

            if max_token == 'ETH' and wrapper_counter == 1:
                continue
            elif max_token == 'WETH' and wrapper_counter == 1:
                self.logger_msg(*self.client.acc_info, msg=f"Current balance in WETH, running unwrap")

            percent = round(random.uniform(*AMOUNT_PERCENT_WRAPS), 9) / 100 if max_token == 'ETH' else 1
            amount_in_wei = int(wallet_balance[max_token][0] * percent)
            amount = self.client.custom_round(amount_in_wei / 10 ** 18, 6)

            if max_token == 'ETH':
                msg = f'Wrap {amount:.6f} ETH'
                from_token_name, to_token_name = 'ETH', 'WETH'
            else:
                msg = f'Unwrap {amount:.6f} WETH'
                from_token_name, to_token_name = 'WETH', 'ETH'

            self.logger_msg(*self.client.acc_info, msg=msg)

            if (max_token == 'ETH' and valid_wallet_balance[max_token] > 1
                    or max_token == 'WETH' and valid_wallet_balance[max_token] != 0):
                data = from_token_name, to_token_name, amount, amount_in_wei
                counter = 0
                result = False
                while True:
                    module_func = random.choice(func)
                    try:
                        result = await module_func(self.client.account_name, self.client.private_key,
                                                   self.client.network, self.client.proxy_init, swapdata=data)
                        wrapper_counter += 1
                    except:
                        pass
                    if result or counter == 3:
                        break

            else:
                self.logger_msg(*self.client.acc_info, msg=f"{from_token_name} balance is too low (lower 1$)")

        return True

    @helper
    async def swaps_abuser(self):
        from functions import swap_odos, swap_oneinch, swap_xyfinance

        func = {
            'Base': [swap_odos, swap_oneinch],
            'Linea': [swap_xyfinance],
            'Scroll': [swap_xyfinance],
            'zkSync': [swap_odos, swap_oneinch]
        }[self.client.network.name]

        current_tokens = list(TOKENS_PER_CHAIN[self.client.network.name].items())[:2]

        wrapper_counter = 0
        for _ in range(2):
            wallet_balance = {k: await self.client.get_token_balance(k, False) for k, v in current_tokens}
            valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
            eth_price = await self.client.get_token_price('ethereum')

            if 'ETH' in valid_wallet_balance:
                valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

            if 'WETH' in valid_wallet_balance:
                valid_wallet_balance['WETH'] = valid_wallet_balance['WETH'] * eth_price

            max_token = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])

            if max_token == 'ETH' and wrapper_counter == 1:
                continue
            elif max_token == 'WETH' and wrapper_counter == 1:
                self.logger_msg(*self.client.acc_info, msg=f"Current balance in WETH, running unwrap")

            percent = round(random.uniform(*AMOUNT_PERCENT_WRAPS), 9) / 100 if max_token == 'ETH' else 1
            amount_in_wei = int(wallet_balance[max_token][0] * percent)
            amount = self.client.custom_round(amount_in_wei / 10 ** 18, 6)

            if max_token == 'ETH':
                msg = f'Wrap {amount:.6f} ETH'
                from_token_name, to_token_name = 'ETH', 'WETH'
            else:
                msg = f'Unwrap {amount:.6f} WETH'
                from_token_name, to_token_name = 'WETH', 'ETH'

            self.logger_msg(*self.client.acc_info, msg=msg)

            if (max_token == 'ETH' and valid_wallet_balance[max_token] > 1
                    or max_token == 'WETH' and valid_wallet_balance[max_token] != 0):
                data = from_token_name, to_token_name, amount, amount_in_wei
                counter = 0
                result = False
                while True:
                    module_func = random.choice(func)
                    try:
                        result = await module_func(self.client.account_name, self.client.private_key,
                                                   self.client.network, self.client.proxy_init, swapdata=data)
                        wrapper_counter += 1
                    except:
                        pass
                    if result or counter == 3:
                        break

            else:
                self.logger_msg(*self.client.acc_info, msg=f"{from_token_name} balance is too low (lower 1$)")

        return True

    @helper
    async def smart_bridge_l0(self, dapp_id: int = None, dust_mode: bool = False):
        from functions import Stargate

        input_list = STARGATE_CHAINS
        replacement_map = {1: 1, 2: 7, 3: 31}
        for num in input_list:
            if num not in replacement_map:
                raise ValueError(f"Invalid number {num} in list. Allowed numbers: {list(replacement_map.keys())}")
        output_list = [replacement_map[num] for num in input_list]

        class_name, tokens, chains, amounts = {
            1: (Stargate, STARGATE_TOKENS, output_list, STARGATE_AMOUNT),
        }[dapp_id]

        converted_chains = copy.deepcopy(chains)
        if any([isinstance(item, tuple) for item in chains]):
            new_chains = []
            for item in chains:
                if isinstance(item, tuple):
                    new_chains.extend(item)
                else:
                    new_chains.append(item)
            converted_chains = new_chains

        start_chain = None
        used_chains = []
        result_list = []
        count_copy = copy.deepcopy(L0_BRIDGE_COUNT)
        total_bridge_count = random.choice(count_copy) if isinstance(count_copy, list) else count_copy
        for bridge_count in range(total_bridge_count):
            while True:
                try:
                    current_client, index, balance, balance_in_wei, balances_in_usd = await self.balance_searcher(
                        converted_chains, tokens, omni_check=True
                    )

                    from_token_name = tokens[index]

                    if dapp_id == 1:

                        if any([isinstance(path, tuple) for path in chains]):
                            tuple_chains = chains[-1]
                            if not isinstance(tuple_chains, tuple) and not all(
                                    isinstance(chain, int) for chain in chains[0: -1]
                            ) and len(chains) != 2:
                                setting_format = '[chain, chain, ..., (chain, chain, ...)]'
                                raise SoftwareExceptionWithoutRetry(
                                    f'This mode on Stargate Bridges support only {setting_format} format'
                                )

                            if bridge_count + 1 == total_bridge_count:
                                final_chains = [chain for chain in chains if isinstance(chain, int)]
                                available_chains = [
                                    chain for chain in final_chains if chain != converted_chains[index]
                                ]
                                dst_chain = random.choice(available_chains)
                            elif bridge_count + 1 == 1:
                                dst_chain = tuple_chains[0]
                            else:
                                available_tuple_chains = [
                                    chain for chain in tuple_chains if chain != converted_chains[index]
                                ]
                                dst_chain = random.choice(available_tuple_chains)
                        elif isinstance(chains, tuple):
                            if total_bridge_count != len(chains) - 1:
                                raise SoftwareExceptionWithoutRetry('L0_BRIDGE_COUNT != all chains in params - 1')
                            dst_chain = converted_chains[bridge_count + 1]
                        else:
                            if not start_chain:
                                start_chain = converted_chains[index]
                            used_chains.append(start_chain)

                            if len(used_chains) >= len(chains):
                                dst_chain = random.choice(
                                    [chain for chain in converted_chains if chain != converted_chains[index]])
                            else:
                                available_chains = [chain for chain in converted_chains if chain not in used_chains]
                                dst_chain = random.choice(available_chains)

                            used_chains.append(dst_chain)

                    else:
                        if isinstance(chains, tuple):
                            if total_bridge_count != len(chains) - 1:
                                raise SoftwareExceptionWithoutRetry('L0_BRIDGE_COUNT != all chains in params - 1')
                            dst_chain = converted_chains[bridge_count + 1]
                        elif converted_chains[index] == 11:
                            if len(converted_chains) == 2:
                                dst_chain = random.choice([chain for chain in converted_chains if chain != 11])
                            elif len(converted_chains) == 3:
                                if 11 in [converted_chains[0], converted_chains[-1]] and converted_chains[1] != 11:
                                    raise SoftwareExceptionWithoutRetry(
                                        'This mode on CoreDAO bridges support only "[chain, 11(CoreDAO), chain]" format')
                                dst_chain = converted_chains[-1]
                                if len(used_chains) == 3:
                                    dst_chain = converted_chains[0]
                                    used_chains = []
                            else:
                                raise SoftwareExceptionWithoutRetry(
                                    'CoreDAO bridges support only 2 or 3 chains in list')
                        else:
                            dst_chain = 11

                        used_chains.append(dst_chain)

                    src_chain_name = current_client.network.name
                    dst_chain_name, dst_chain_id, _, _ = OMNICHAIN_NETWORKS_DATA[dst_chain]
                    to_token_name = tokens[converted_chains.index(dst_chain)]

                    if src_chain_name == dst_chain_name:
                        raise SoftwareException(
                            f'Can`t bridge into same network: SRC Chain:{src_chain_name}, DST Chain:{dst_chain_name}'
                        )

                    if from_token_name != 'ETH':
                        contract = current_client.get_contract(
                            TOKENS_PER_CHAIN2[current_client.network.name][from_token_name])
                        decimals = await contract.functions.decimals().call()
                    else:
                        decimals = 18

                    amount_in_wei = self.client.to_wei((
                        await current_client.get_smart_amount(amounts, token_name=tokens[index], omnicheck=True)
                    ), decimals)

                    if dust_mode:
                        amount_in_wei = int(amount_in_wei * random.uniform(0.0000001, 0.0000003))

                    amount = f"{amount_in_wei / 10 ** decimals:.4f}"

                    swapdata = (src_chain_name, dst_chain_name, dst_chain_id,
                                from_token_name, to_token_name, amount, amount_in_wei)

                    result_list.append(await class_name(current_client).bridge(swapdata=swapdata))

                    if current_client:
                        await current_client.session.close()

                    if total_bridge_count != 1:
                        await sleep_tools(self)

                    break

                except Exception as error:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Error during the route. Will try again in 1 min... Error: {error}", type_msg='warning'
                    )
                    await asyncio.sleep(60)

        if total_bridge_count != 1:
            return all(result_list)
        return any(result_list)

    @helper
    async def swap_bridged_usdc(self):
        from functions import swap_uniswap

        amount_in_wei, amount, _ = await self.client.get_token_balance('USDC.e')
        data = 'USDC.e', 'USDC', amount, amount_in_wei

        if amount_in_wei == 0:
            raise SoftwareException("Insufficient USDC balances")

        return await swap_uniswap(self.client.account_name, self.client.private_key,
                                  self.client.network, self.client.proxy_init, swapdata=data)

   
    async def balance_searcher(
            self, chains, tokens=None, omni_check: bool = True, native_check: bool = False, silent_mode: bool = False,
            balancer_mode: bool = False
    ):
        index = 0
        clients = []
        while True:
            try:
                clients = [await self.client.new_client(OMNICHAIN_WRAPED_NETWORKS[chain] if omni_check else chain)
                           for chain in chains]

                if native_check:
    
                    tokens = [client.token for client in clients]

                balances = [await client.get_token_balance(
                    omnicheck=omni_check if token not in ['USDV', 'STG', 'MAV', 'CORE'] else True, token_name=token,
                )
                            for client, token in zip(clients, tokens)]
                
                if all(balance_in_wei == 0 for balance_in_wei, _, _ in balances) and not balancer_mode:
                    raise SoftwareException('Insufficient balances in all networks!')

                balances_in_usd = []
                for balance_in_wei, balance, token_name in balances:
                    token_price = 1
                    if 'USD' not in token_name:
                        token_price = await self.client.get_token_price(COINGECKO_TOKEN_API_NAMES[token_name])
                    balance_in_usd = balance * token_price
                    balances_in_usd.append([balance_in_usd, token_price])

                index = balances_in_usd.index(max(balances_in_usd, key=lambda x: x[0]))

                for index_client, client in enumerate(clients):
                    if index_client != index:
                        await client.session.close()

                if not silent_mode:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Detected {round(balances[index][1], 5)} {tokens[index]} in {clients[index].network.name}",
                        type_msg='success'
                    )

                return clients[index], index, balances[index][1], balances[index][0], balances_in_usd[index]

            except (aiohttp.client_exceptions.ClientProxyConnectionError, asyncio.exceptions.TimeoutError,
                    aiohttp.client_exceptions.ClientHttpProxyError, python_socks.ProxyError):
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Connection to RPC is not stable. Will try again in 1 min...",
                    type_msg='warning'
                )
                await asyncio.sleep(60)
            except SoftwareException as error:
                raise error
            except Exception as error:
                traceback.print_exc()
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Bad response from RPC. Will try again in 1 min... Error: {error}", type_msg='warning'
                )
                await asyncio.sleep(60)
            finally:
                for index_client, client in enumerate(clients):
                    if index_client != index:
                        await client.session.close()


    
    @helper
    async def full_multi_swap_bebop(self):
        from functions import one_to_many_swap_bebop, many_to_one_swap_bebop
        token_names = await one_to_many_swap_bebop(self.client.account_name, self.client.private_key,
                                                   self.client.network, self.client.proxy_init)

        if token_names:
            await sleep_tools(self)
            return await many_to_one_swap_bebop(self.client.account_name, self.client.private_key, self.client.network,
                                                self.client.proxy_init, from_token_names=token_names)

        else:
            self.logger_msg(*self.client.acc_info, msg=f"Unable to perform full multi swap")
