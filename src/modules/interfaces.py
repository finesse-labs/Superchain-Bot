import asyncio

from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector
from loguru import logger
from sys import stderr
from datetime import datetime
from abc import ABC, abstractmethod
from random import uniform
from config import CHAIN_NAME




def get_user_agent():
    random_version = f"{uniform(520, 540):.2f}"
    return (f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random_version} (KHTML, like Gecko)'
            f' Chrome/123.0.0.0 Safari/{random_version} Edg/123.0.0.0')


class PriceImpactException(Exception):
    pass


class SoftwareExceptionHandled(Exception):
    pass


class BlockchainException(Exception):
    pass


class BlockchainExceptionWithoutRetry(Exception):
    pass


class SoftwareException(Exception):
    pass


class CriticalException(Exception):
    pass


class SoftwareExceptionWithoutRetry(Exception):
    pass


class SoftwareExceptionWithRetries(Exception):
    pass


class InsufficientBalanceException(Exception):
    pass


class BridgeExceptionWithoutRetry(Exception):
    pass


class DepositExceptionWithoutRetry(Exception):
    pass


class Logger(ABC):
    def __init__(self):
        self.logger = logger
        self.logger.remove()
        logger_format = "<cyan>{time:HH:mm:ss}</cyan> | <level>" "{level: <8}</level> | <level>{message}</level>"
        self.logger.add(stderr, format=logger_format)
        date = datetime.today().date()
        self.logger.add(f"./data/logs/{date}.log", rotation="500 MB", level="INFO", format=logger_format)

    def logger_msg(self, account_name, address, msg, chain_name=None, from_token=None, to_token=None, type_msg: str = 'info'):
        class_name = self.__class__.__name__

        # Базовая информация
        info = f"{class_name} | [{address}]"
        
        # Добавляем сеть, если указана
        if chain_name:
            info += f" | [{chain_name}]"
        
        # Добавляем токены, если указаны
        if from_token and to_token:
            info += f" | [{from_token} => {to_token}]"
        
        # Вывод лога в зависимости от типа
        if type_msg == 'info':
            self.logger.info(f"{info} | {msg}")
        elif type_msg == 'error':
            self.logger.error(f"{info} | {msg}")
        elif type_msg == 'success':
            self.logger.success(f"{info} | {msg}")
        elif type_msg == 'warning':
            self.logger.warning(f"{info} | {msg}")


class DEX(ABC):
    @abstractmethod
    async def swap(self):
        pass

    @abstractmethod
    async def deposit(self):
        pass

    @abstractmethod
    async def withdraw(self):
        pass

    async def make_request(self, method:str = 'GET', url:str = None, data:str = None, params:dict = None,
                           headers:dict = None, json:dict = None, module_name:str = 'Request',
                           content_type:str | None = "application/json"):

        insf_balance_code = {
            'BingX': [100437],
            'Binance': [4026],
            'Bitget': [43012, 13004],
            'OKX': [58350],
        }[self.class_name]


class RequestClient(ABC):
    def __init__(self, client):
        self.client = client

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None):

        headers = (headers or {}) | {'User-Agent': get_user_agent()}
        async with self.client.session.request(method=method, url=url, headers=headers, data=data,
                                               params=params, json=json) as response:
            try:
                data = await response.json()

                if response.status == 200:
                    return data
                raise SoftwareException(
                    f"Bad request to {self.__class__.__name__} API. "
                    f"Response status: {response.status}. Response: {await response.text()}")
            except Exception as error:
                raise SoftwareException(
                    f"Bad request to {self.__class__.__name__} API. "
                    f"Response status: {response.status}. Response: {await response.text()} Error: {error}")


class Refuel(ABC):
    @abstractmethod
    async def refuel(self, *args, **kwargs):
        pass


class Messenger(ABC):
    @abstractmethod
    async def send_message(self):
        pass


class Landing(ABC):
    @abstractmethod
    async def deposit(self):
        pass

    @abstractmethod
    async def withdraw(self):
        pass


class Minter(ABC):
    @abstractmethod
    async def mint(self, *args, **kwargs):
        pass


class Creator(ABC):
    @abstractmethod
    async def create(self):
        pass


class Blockchain(ABC):
    def __init__(self, client):
        self.client = client

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None):

        headers = (headers or {}) | {'User-Agent': get_user_agent()}
        async with self.client.session.request(method=method, url=url, headers=headers, data=data,
                                               params=params, json=json) as response:

            data = await response.json()
            if response.status == 200:
                return data
            raise SoftwareException(
                f"Bad request to {self.__class__.__name__} API. "
                f"Response status: {response.status}. Status: {response.status}. Response: {await response.text()}")