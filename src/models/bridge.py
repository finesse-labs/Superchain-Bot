from __future__ import annotations

import random
from typing import List, Any, Dict

from pydantic import BaseModel, model_validator

from src.models.token import Token
from src.models.chain import Chain


class BridgeConfig(BaseModel):
    from_chain: Chain
    to_chain: Chain

    from_token: Token
    to_token: Token

    amount: float | List[float]

    use_percentage: bool
    bridge_percentage: float | List[float]

    @model_validator(mode='before')
    @classmethod
    def set_fields(cls, values: dict[str, Any]) -> Dict[str, Any]:
        amount = values.get('amount')
        bridge_percentage = values.get('bridge_percentage')

        if isinstance(amount, List):
            amount = random.uniform(amount[0], amount[1])
            values['amount'] = amount

        if isinstance(bridge_percentage, List):
            bridge_percentage = random.uniform(
                bridge_percentage[0], bridge_percentage[1]
            )
            values['bridge_percentage'] = bridge_percentage

        return values
