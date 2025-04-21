from __future__ import annotations

from pydantic import BaseModel


class Chain(BaseModel):
    chain_name: str
    native_token: str
    rpc: str
    chain_id: int
