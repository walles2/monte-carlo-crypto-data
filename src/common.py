from typing import NamedTuple
from datetime import datetime

class PriceRecord(NamedTuple):
    market_type: str
    market_name: str
    metric: str
    value: float
    timestamp: datetime
