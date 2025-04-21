from dataclasses import dataclass


@dataclass
class ERC20:
    abi: str = open('./assets/abi/erc20.json', 'r').read()


@dataclass
class SuperBridgeData:
    address: str = None
    abi: str = None


@dataclass
class AcrossBridgeData:
    address: str = '0x09aea4b2242abC8bb4BB78D537A67a245A7bEC64'
    abi: str = open('./assets/abi/across.json', 'r').read()


@dataclass
class MatchaSwapData:
    address: str = None
    abi: str = None


@dataclass
class BungeeSwapData:
    address: str = None
    abi: str = None


@dataclass
class SushiswapData:
    address: str = None
    abi: str = None


@dataclass
class OwltoData:
    address: str = None
    abi: str = None


@dataclass
class OkuData:
    address: str = None
    abi: str = None


@dataclass
class DefillamaData:
    address: str = None
    abi: str = None


@dataclass
class RelayData:
    address: str = None
    abi: str = None


@dataclass
class VenusData:
    abi: str = open('./assets/abi/venus.json', 'r').read()


@dataclass
class WrapData:
    abi: str = open('./assets/abi/eth.json', 'r').read()


@dataclass
class InkySwapData:
    address: str = '0xA8C1C38FF57428e5C3a34E0899Be5Cb385476507'
    abi: str = open('./assets/abi/inky.json', 'r').read()


@dataclass
class InkGMData:
    address: str = '0x9F500d075118272B3564ac6Ef2c70a9067Fd2d3F'
    abi: str = open('./assets/abi/ink_gm.json', 'r').read()


@dataclass
class RubyScoreData:
    base_address: str = '0xe10Add2ad591A7AC3CA46788a06290De017b9fB4'
    zora_address: str = '0xDC3D8318Fbaec2de49281843f5bba22e78338146'
    abi: str = open('./assets/abi/rubyscore.json', 'r').read()


@dataclass
class DeployData:
    abi: str = open('./assets/abi/deploy.json', 'r').read()
