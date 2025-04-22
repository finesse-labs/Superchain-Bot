#==============================================================================================================

# --- Superchain settings -- #
# Выполнение транзакций по отдельным чейнам, по спискам активностей из RandomDailyTxConfig

TASKS = ["CLAIM_BADGES"]

TEST = [
    ["BASE_RANDOM_TX"]
]

MULTICHAIN_ACTIVITY = [
    ["OKX_WITHDRAW"],                                  
    (
        ["BASE_RANDOM_TX", "ZORA_RANDOM_TX"],          
        ["SONEIUM_RANDOM_TX", "LISK_RANDOM_TX"]       
    ),                                                                                   
    ["SWELL_RANDOM_TX", "UNICHAIN_RANDOM_TX"]
]

BRIDGE_CLAIM_SIMPLE = [
    ["OKX_WITHDRAW"],                                  
    ["STARGATE_BRIDGE", "DISPERSE_BRIDGE"],             
    ["CLAIM_BADGES"]                             
]


OKX_WITHDRAW = ["OKX_WITHDRAW"]
DISPERSE_BRIDGE = ["DISPERSE_BRIDGE"]
BASE_RANDOM_TX = ["BASE_RANDOM_TX"]
INK_RANDOM_TX = ["INK_RANDOM_TX"]
OP_RANDOM_TX = ["OP_RANDOM_TX"]
LISK_RANDOM_TX = ["LISK_RANDOM_TX"]
UNICHAIN_RANDOM_TX = ["UNICHAIN_RANDOM_TX"]
SONEIUM_RANDOM_TX = ["SONEIUM_RANDOM_TX"]
ZORA_RANDOM_TX = ["ZORA_RANDOM_TX"]
SWELL_RANDOM_TX = ["SWELL_RANDOM_TX"]
STARGATE_BRIDGE  = ["STARGATE_BRIDGE"]

CLAIM_BADGES = ["CLAIM_BADGES"]

# Explanation:
# - TASKS: The top-level list of tasks to execute.
# - [ ]: Only one task from the list is chosen randomly.
# - ( ): All tasks inside are executed in random order.
# - Single string: Executes as is.
# - 'OKX_WITHDRAW', 'DISPERSE_BRIDGE' - use only first
# - Module-specific settings are in config.py

#==============================================================================================================