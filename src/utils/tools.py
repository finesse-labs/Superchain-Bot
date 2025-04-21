import io
import os
import sys
import json
import random
import asyncio
import functools
import traceback
import msoffcrypto
import pandas as pd

from getpass import getpass

from python_socks._protocols.errors import ReplyError

from src.utils.networks import *
from termcolor import cprint
from python_socks import ProxyError
from datetime import datetime, timedelta
from asyncio.exceptions import TimeoutError
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import ContractLogicError
from aiohttp import ClientSession, TCPConnector, ClientResponseError
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError
from aiohttp.client_exceptions import ClientProxyConnectionError, ClientHttpProxyError, ClientError

from config import (
    SLEEP_TIME_MODULES,
    SLEEP_TIME_RETRY,
    MAXIMUM_RETRY
)


async def sleep_tools(self, min_time=SLEEP_TIME_MODULES[0], max_time=SLEEP_TIME_MODULES[1]):
    duration = random.randint(min_time, max_time)
    print()
    self.logger_msg(*self.client.acc_info, msg=f"💤 Sleeping for {duration} seconds")
    await asyncio.sleep(duration)


def clean_progress_file():
    with open('./data/services/wallets_progress.json', 'w') as file:
        file.truncate(0)


def clean_google_progress_file():
    with open('./data/services/google_progress.json', 'w') as file:
        file.truncate(0)


def clean_gwei_file():
    with open('./data/services/maximum_gwei.json', 'w') as file:
        file.truncate(0)


def check_progress_file():
    file_path = './data/services/wallets_progress.json'

    if os.path.getsize(file_path) > 0:
        return True
    else:
        return False


def check_google_progress_file():
    file_path = './data/services/google_progress.json'

    if os.path.getsize(file_path) > 0:
        return True
    else:
        return False


def drop_date():
    current_date = datetime.now()
    random_months = random.randint(1, 4)

    future_date = current_date + timedelta(days=random_months * 30)

    return future_date.strftime("%Y.%m.%d")


def create_cex_withdrawal_list():
    from config import ACCOUNT_NAMES, CEX_WALLETS
    cex_data = {}

    if ACCOUNT_NAMES and CEX_WALLETS:
        with open('./data/services/cex_withdraw_list.json', 'w') as file:
            for account_name, cex_wallet in zip(ACCOUNT_NAMES, CEX_WALLETS):
                cex_data[str(account_name)] = cex_wallet
            json.dump(cex_data, file, indent=4)
        cprint('✅ Successfully added and saved CEX wallets data', 'light_blue')
        cprint('⚠️ Check all CEX deposit wallets by yourself to avoid problems', 'light_yellow', attrs=["blink"])
    else:
        cprint('❌ Put your wallets into files, before running this function', 'light_red')


def get_wallet_for_deposit(self):
    from src.modules.interfaces import CriticalException

    try:
        with open('./data/services/cex_withdraw_list.json') as file:
            from json import load
            cex_withdraw_list = load(file)
            cex_wallet = cex_withdraw_list[self.client.account_name]
        return cex_wallet
    except json.JSONDecodeError:
        from src.modules.interfaces import CriticalException
        raise CriticalException(f"Bad data in cex_wallet_list.json")
    except Exception as error:
        raise CriticalException(f'There is no wallet listed for deposit to CEX: {error}')


def helper(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        from src.modules.interfaces import (
            BlockchainException, SoftwareException, SoftwareExceptionWithoutRetry,
            BlockchainExceptionWithoutRetry, SoftwareExceptionHandled
        )

        attempts = 0
        k = 0

        no_sleep_flag = False
        try:
            while attempts <= MAXIMUM_RETRY:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as error:
                    attempts += 1
                    k += 1
                    msg = f'{error}'
                    # traceback.print_exc()

                    if isinstance(error, KeyError):
                        msg = f"Parameter '{error}' for this module is not exist in software!"
                        self.logger_msg(*self.client.acc_info, msg=msg, type_msg='error')
                        return False

                    elif any(keyword in str(error) for keyword in (
                            'Bad Gateway', '403', 'SSL', 'Invalid proxy', 'rate limit', '429', '407', '503'
                    )):
                        self.logger_msg(*self.client.acc_info, msg=msg, type_msg='warning')
                        await self.client.change_proxy()
                        continue

                    elif 'Error code' in str(error):
                        msg = f'{error}. Will try again...'

                    elif 'Server disconnected' in str(error):
                        msg = f'{error}. Will try again...'

                    elif 'StatusCode.UNAVAILABLE' in str(error):
                        msg = f'RPC got autism response, will try again......'

                    elif '<html lang="en">' in str(error):
                        msg = f'Proxy got non-permanent ban, will try again...'

                    elif isinstance(error, SoftwareExceptionHandled):
                        self.logger_msg(*self.client.acc_info, msg=f"{error}", type_msg='warning')
                        return True

                    elif isinstance(error, (SoftwareExceptionWithoutRetry, BlockchainExceptionWithoutRetry)):
                        self.logger_msg(self.client.account_name, None, msg=msg, type_msg='error')
                        return False

                    elif isinstance(error, SoftwareException):
                        msg = f'{error}'

                    elif isinstance(error, BlockchainException):
                        if 'insufficient funds' not in str(error):
                            self.logger_msg(
                                self.client.account_name,
                                None, msg=f'Maybe problem with node: {self.client.rpc}', type_msg='warning'
                            )
                            await self.client.change_rpc()

                    elif isinstance(error, (ClientError, asyncio.TimeoutError, ProxyError, ReplyError)):
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Connection to RPC is not stable. Will try again in 10 seconds...",
                            type_msg='warning'
                        )
                        await asyncio.sleep(10)
                        self.logger_msg(*self.client.acc_info, msg=msg, type_msg='warning')

                        if k % 2 == 0:
                            await self.client.change_proxy()
                            await self.client.change_rpc()
                        attempts -= 1

                        continue

                    else:
                        msg = f'Unknown Error: {error}'
                        traceback.print_exc()

                    self.logger_msg(
                        self.client.account_name, None, msg=f"{msg} | Try[{attempts}/{MAXIMUM_RETRY + 1}]",
                        type_msg='error'
                    )

                    if attempts > MAXIMUM_RETRY:
                        self.logger_msg(
                            self.client.account_name, None,
                            msg=f"Tries are over, software will stop module\n", type_msg='error'
                        )
                        break
                    else:
                        if not no_sleep_flag:
                            await sleep_tools(self, *SLEEP_TIME_RETRY)

        finally:
            await self.client.session.close()
        return False
    return wrapper


def gas_checker(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        return await func(self, *args, **kwargs)

    return wrapper


async def get_eth_price():
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price'

        params = {
            'ids': 'ethereum',
            'vs_currencies': 'usd'
        }

        async with ClientSession(connector=TCPConnector(verify_ssl=False)) as session:
            async with session.get(url=url, params=params) as response:
                data = await response.json()
                if response.status == 200:
                    return data['ethereum']['usd']
    except Exception as error:
        cprint(f'\nError in <get_eth_price> function! Error: {error}\n', color='light_red')
        sys.exit()
