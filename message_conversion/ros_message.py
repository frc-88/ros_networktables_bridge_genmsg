from typing import List, Protocol


class RosMessage(Protocol):
    _type: str
    _slot_types: List[str]
    __slots__: List[str]
