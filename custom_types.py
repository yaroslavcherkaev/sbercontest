""" мои типы данных """
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class AssetPrice(Enum):
    """Котировальный список активов."""
    ASSETS = ["LKOH", "SBER", "GAZP", "VTBR"]
    LKOH = Decimal(5896)
    SBER = Decimal(250)
    GAZP = Decimal(180)
    VTBR = Decimal('0.028974')
    lot_weight = 10


@dataclass
class Order:
    """Тип заявка содержит информацию: номер заявки, id профиля
    тип заявки (BUY | SELL), название актива, кол-во лотов (лот == 10 шт.), стоимость."""
    order_id: str = None
    user_id: int = None
    order_type: str = None
    asset_name: str = None
    lots: int = None
    price: Decimal = None
