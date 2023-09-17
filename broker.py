"""модуль с функциями, которые симмулируют работу брокеров"""
from custom_types import Order, AssetPrice
import db_requests
import datetime

from decimal import Decimal


def check_balance(order: Order, balance: Decimal) -> bool:
    """функция проверки достаточно ли у пользователя денег на балансе"""
    user_active_orders = db_requests.fetchall_by_id("reg_orders", ["type", "price", "status"], order.user_id)
    if len(user_active_orders) != 0:
        on_hold = 0
        for row in user_active_orders:
            if row["type"] == "BUY" and row["status"] == "ACTIVE":
                on_hold += Decimal(row["price"])
        balance = balance - on_hold
    if balance >= order.price:
        return True
    else:
        return False


def check_assets(order: Order, user_lots: int) -> bool:
    """функция проверки достаточно ли у пользователя акций"""
    user_active_orders = db_requests.fetchall_by_id_and_asset("reg_orders", ["type", "status", "lots"],
                                                              order.user_id, order.asset_name)
    if len(user_active_orders) != 0:
        on_hold = 0
        for row in user_active_orders:
            if row["type"] == "SELL" and row["status"] == "ACTIVE":
                on_hold += int(row["lots"])
        user_lots = user_lots - on_hold
    if user_lots >= order.lots:
        return True
    else:
        return False


def create_buy_order(order: Order) -> bool:
    """функция создания заявки на покупку"""
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    now_formatted = now.strftime('%Y-%m-%d %H:%M:%S')
    db_requests.insert("reg_orders", {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "type": order.order_type,
            "asset": order.asset_name,
            "price": str(order.price),
            "lots": order.lots,
            "status": "ACTIVE",
            "date": now_formatted
        })
    return True


def create_sell_order(order: Order) -> bool:
    """функция создания заявки на покупку"""
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    now_formatted = now.strftime('%Y-%m-%d %H:%M:%S')
    db_requests.insert('reg_orders', {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "type": order.order_type,
            "asset": order.asset_name,
            "price": str(order.price),
            "lots": order.lots,
            "status": "ACTIVE",
            "date": now_formatted
        })
    return True
