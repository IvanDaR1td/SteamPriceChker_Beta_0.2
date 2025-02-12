from dataclasses import dataclass
from datetime import datetime

@dataclass
class TrackedGame:
    appid: int
    name: str
    initial_price: float
    last_checked: datetime
    channel_id: int