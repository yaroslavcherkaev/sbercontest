"""модуль симмулирующий торговлю на бирже."""
import exceptions
from custom_types import Order, AssetPrice
import db_requests
import profile
from decimal import Decimal


def do_exchange(order: Order, offer: Order) -> None:
    """Функция обмена акциями и деньгами между аккаунтами"""
    price = Decimal(order.price)
    pcs = order.lots * AssetPrice.lot_weight.value
    match order.order_type:
        case "BUY":
            profile.change_balance(order.user_id, price * -1)
            profile.change_balance(offer.user_id, price)
            profile.change_asset_pcs(order, pcs)
            profile.change_asset_pcs(offer, pcs * -1)
            return
        case "SELL":
            profile.change_balance(order.user_id, price)
            profile.change_balance(offer.user_id, price * -1)
            profile.change_asset_pcs(order, pcs * -1)
            profile.change_asset_pcs(offer, pcs)
            return
        case _:
            return


def deal_with_issuer(order: Order) -> None:
    """Функция обмена акциями и деньгами с эмитентом"""
    price = Decimal(order.price)
    pcs = order.lots * AssetPrice.lot_weight.value
    match order.order_type:
        case 'BUY':
            profile.change_balance(order.user_id, price * -1)
            profile.change_asset_pcs(order, pcs)
        case 'SELL':
            """продать акции эмитенту нельзя"""
            return
        case _:
            return


def close_the_deal(order: Order) -> None:
    """заключение сделки, если активных от людей нет то сделка заключается с эмитентом (просто зачисляются акции)"""
    try:
        offer = db_requests.select_active_offer(order) 
        do_exchange(order, offer)
    except exceptions.ExchangerException:
        deal_with_issuer(order)

