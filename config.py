MOBILE_PROXY = False  # True - мобильные proxy/False - обычные proxy
ROTATE_IP = False  # Настройка только для мобильных proxy
SLIPPAGE = 0.03

TG_BOT_TOKEN = ''  # str ('1234567890:abcde2VHUAfnD6vEbCeLHONvFIbdACBMJ5U')
TG_USER_ID = None  # int (1234567890) or None

# TASKS
from tasks import * 

SHUFFLE_WALLETS = True
PAUSE_BETWEEN_WALLETS = [40, 100]
PAUSE_BETWEEN_MODULES = [40, 125]
RETRIES = 3  # Сколько раз повторять 'зафейленное' действие
PAUSE_BETWEEN_RETRIES = 15  # Пауза между повторами
WAIT_FOR_RECEIPT = True     # Если True, будет ждать получения средств во входящей сети перед запуском очередного модуля


# STARGATE BRIDGE
STARGATE_AMOUNT = ('72', '95') # Сумма в количестве - (0.01, 0.02), в процентах - ("10", "20")
STARGATE_CHAINS = [1, 2] # Arbitrum -> 1, Base -> 2, Optimism -> 3
STARGATE_TOKENS = ['ETH', 'ETH'] # ETH
L0_BRIDGE_COUNT = 1 # Количество бриджей для одного запуска


# ONCHAIN ACTIVITIES
class RandomDailyTxConfig:
    BASE_MODULES = [
        'UNISWAP',
        'MATCHA_SWAP',
        'SUSHI_SWAP',
        'BUNGEE_SWAP',
        'OWLTO_SWAP',
        'RELAY_SWAP',
        'OKU_SWAP',
        'DEFILLAMA_SWAP',
        'RUBYSCORE_VOTE',  # Голосование https://rubyscore.io/dashboard
        'WRAPPER_UNWRAPPER',  # Врап->Анврап ETH
        'CONTRACT_DEPLOY',  # Деплой контракта

        'RANDOM_TXS',  # Выполняет случайные транзакции из списка указанных модулей | RandomTransactionsSettings
        'RANDOM_SWAPS',
        # Выполняет свапы ETH -> *Случайный токен* | RandomSwapsSettings (добавление токенов src->utils->data->tokens)
        'SWAP_ALL_TO_ETH'  # Свапает все токены в ETH.
    ]
    INK_MODULES = [
        'WRAPPER_UNWRAPPER',
        'INK_GM',

        'RANDOM_TXS',
        'RANDOM_SWAPS',
        'SWAP_ALL_TO_ETH'
    ]
    LISK_MODULES = [
        'WRAPPER_UNWRAPPER',

        'RANDOM_TXS',
        'SWAP_ALL_TO_ETH'
    ]
    OPTIMISM_MODULES = [
        'WRAPPER_UNWRAPPER',

        'RANDOM_TXS',
        'RANDOM_SWAPS',
        'SWAP_ALL_TO_ETH'
    ]
    UNICHAIN_MODULES = [
        'WRAPPER_UNWRAPPER',
        'VENUS_WITHDRAW',

        'RANDOM_TXS',
        'RANDOM_SWAPS',
        'SWAP_ALL_TO_ETH'
    ]
    SONEIUM_MODULES = [
        'WRAPPER_UNWRAPPER',

        'RANDOM_TXS',
        'RANDOM_SWAPS',
        'SWAP_ALL_TO_ETH',
    ]
    ZORA_MODULES = [
        'WRAPPER_UNWRAPPER',
        'RUBYSCORE_VOTE',

        'RANDOM_TXS',
        'RANDOM_SWAPS',
        'SWAP_ALL_TO_ETH'
    ]
    SWELL_MODULES = [
        'WRAPPER_UNWRAPPER',

        'RANDOM_TXS',
        'RANDOM_SWAPS',
        'SWAP_ALL_TO_ETH'
    ]

    MODE_MODULES = [
        'WRAPPER_UNWRAPPER',

        'RANDOM_TXS',
        'RANDOM_SWAPS',
        'CONTRACT_DEPLOY',
        'SWAP_ALL_TO_ETH'
    ]


class DisperseChainsSettings:
    base_chain = ['UNICHAIN']  # Сеть из которой будет происходить рассылка
    to_chains = [ 'SONEIUM']
    amount_to_bride = [0.00007, 0.0001]  # Сколько эфира бриджить для каждой сети

    min_balance_in_chains = {
        'BASE': 0.00007,
        'OP': 0.00007,
        'LISK': 0.00007,
        'UNICHAIN': 0.00007,
        'MODE': 0.00007,
        'ZORA': 0.00007,
        'INK': 0.00007,
        'SONEIUM': 0.00007,
        'SWELL': 0.00007,
    }


class RandomSwapsSettings:
    number_of_swaps = [5, 10]
    swap_percentage = [0.03, 0.05]


class RandomTransactionsSettings:
    transactions_by_chain = {
        'BASE': [4, 5],
        'INK': [3, 5],
        'ZORA': [2, 4],
        'OP': [3, 4],
        'LISK': [1, 3],
        'UNICHAIN': [3, 5],
        'SWELL': [2, 3],
        'SONEIUM': [1, 4],
        'MODE': [1, 3],
    }


class SuperBridgeSettings:
    from_chain = ['BASE']
    to_chain = ['UNICHAIN']

    amount = [0.001, 0.002]  # Кол-во ETH [от, до]
    use_percentage = False  # Использовать ли процент от баланса вместо amount
    bridge_percentage = [0.5, 0.5]  # Процент от баланса. 0.1 - это 10%, 0.27 - это 27% и т.д.
    min_eth_balance = 0.01  # Минимальный баланс в сети UNICHAIN. Если выше, то бридж сделан не будет.


class AcrossBridgeSettings:
    from_chain = ['UNICHAIN']
    to_chain = ['BASE']

    amount = [0.001, 0.002]  # Кол-во ETH [от, до]
    use_percentage = False  # Использовать ли процент от баланса вместо amount
    bridge_percentage = [0.01, 0.01]  # Процент от баланса. 0.1 - это 10%, 0.27 - это 27% и т.д.
    min_eth_balance = 1  # Минимальный баланс в сети UNICHAIN. Если выше, то бридж сделан не будет.


class UniswapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]  # 0.1 - 10%, 0.2 - 20%...
    swap_all_balance = False


class InkySwapSettings:
    from_token = ['ETH']
    to_token = ['USDT']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]  # 0.1 - 10%, 0.2 - 20%...
    swap_all_balance = False


class OkuSwapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]  # 0.1 - 10%, 0.2 - 20%...
    swap_all_balance = False


class MatchaSwapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]
    swap_all_balance = False


class BungeeSwapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]
    swap_all_balance = False


class SushiSwapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]
    swap_all_balance = False


class OwltoSwapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]
    swap_all_balance = False


class DefillamaSwapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]
    swap_all_balance = False


class RelaySwapSettings:
    from_token = ['ETH']
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.01, 0.05]
    swap_all_balance = False


class WrapperUnwrapperSettings:
    amount = [0.001, 0.002]
    use_all_balance = True  # Только для unwrap
    use_percentage = True  # Как wrap так и unwrap
    percentage_to_wrap = [0.1, 0.2]


class VenusDepositSettings:
    token = ['USDC']  # USDC / UNI
    percentage_to_deposit = [0.2, 0.5]


class OKXWithdrawSettings:  # Вывод с ОКХ на кошельки
    chain = ['Optimism']  # 'Base' / 'Optimism' / 'Arbitrum One'
    token = 'ETH'
    amount = [0.00104, 0.0011]  # учитывайте минимальный amount 0.00204(BASE), 0.00104(ARB), 0.00014(OP)

    min_eth_balance = 0.001  # Если в 'chain' уже есть больше min_eth_balance, то вывода не будет.


class OKXSettings:
    API_KEY = ''
    API_SECRET = ''
    API_PASSWORD = ''

    PROXY = None  # 'http://login:pass@ip:port' (если нужно)

















# ========================= SCRIPT INFO ========================= 

from src.utils.script_info import *
