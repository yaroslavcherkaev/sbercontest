"""модуль для управления состоянием профиля пользователя"""
import broker
import db_requests
from decimal import Decimal

from sqlite3 import IntegrityError

import exchange
from custom_types import AssetPrice, Order
import exceptions


def onboarding(user_id: int) -> bool:
    """Онбординг"""
    try:
        db_requests.insert("users", {"user_id": user_id})
        return True
    except IntegrityError:
        return False


def get_balance(user_id: int) -> Decimal:
    """Получить сведения о балансе"""
    try:
        balance_dict = db_requests.select("users", ["balance"], user_id)
        balance = Decimal(balance_dict['balance'])
        return balance
    except KeyError:
        db_requests.insert("users", {"user_id": user_id})
        balance = Decimal(0)
        return balance


def get_lots(user_id: int, asset_name: str) -> int:
    try:
        pcs = db_requests.select("users", [asset_name], user_id)[asset_name]
        lots = pcs / AssetPrice.lot_weight.value
        return lots
    except KeyError:
        db_requests.insert("users", {"user_id": user_id})
        return 0


def change_balance(user_id: int, money: Decimal) -> Decimal:
    """Изменить баланс"""
    try:
        balance_dict = db_requests.select("users", ["balance"], user_id)
        balance = Decimal(balance_dict['balance'])
        new_balance = balance + money
        db_requests.update_balance(user_id, str(new_balance))
        return new_balance
    except KeyError:
        db_requests.insert("users", {"user_id": user_id})
        db_requests.update_balance(user_id, str(money))
        return money


def change_asset_pcs(order: Order, difference: int) -> None:
    """Изменить кол-во акций"""
    try:
        asset_dict = db_requests.select("users", [order.asset_name], order.user_id)
        asset_pcs = asset_dict[order.asset_name]
        new_pcs = asset_pcs + difference
        db_requests.update_asset_pcs(order.user_id, order.asset_name, new_pcs)
        db_requests.update_status(order.order_id)
    except KeyError:
        db_requests.insert("users", {"user_id": order.user_id})
        db_requests.update_asset_pcs(order.user_id, order.asset_name, difference)


def get_portfolio(user_id: int) -> dict:
    """Получить сведения о портфеле"""
    asset_list = AssetPrice.ASSETS.value
    portfolio = db_requests.select("users", asset_list, user_id)
    if len(portfolio) != 0:
        value = Decimal(0)
        for asset_name in portfolio.keys():
            value += AssetPrice[asset_name].value * portfolio[asset_name]
        portfolio["value"] = value
        return portfolio
    else:
        db_requests.insert("users", {"user_id": user_id})
        portfolio = db_requests.select("users", asset_list, user_id)
        portfolio["value"] = Decimal(0)
        return portfolio


def parse_order(order: str) -> dict:
    """ Распарсить запрос из телеграмма"""
    parsed_order = {}
    parsed_request = order.split()
    if len(parsed_request) == 2:
        if parsed_request[0] in AssetPrice.ASSETS.value:
            parsed_order['asset'] = parsed_request[0]
        else:
            raise exceptions.NotCorrectMessage(f"Неверный формат. Проверьте написание названия акции.\n"
                                               f"Доустпный список акций: {' '.join(AssetPrice.ASSETS.value)}"
                                               )
        try:
            parsed_order['lots'] = int(parsed_request[1])
        except ValueError:
            raise exceptions.NotCorrectMessage("Неверный формат. Проверьте написание кол-ва лотов. ")
        if parsed_order['lots'] <= 0:
            raise exceptions.NotCorrectMessage(f"Неверный формат. Проверьте написание кол-ва лотов.\n"
                                               f"Число должно быть больше, чем 0"
                                               )
        return parsed_order
    else:
        raise exceptions.NotCorrectMessage(f"Неверный формат. Проверьте написание команды.\n"
                                           f"Команды:\n"
                                           f"/buy asset lots\n"
                                           f"/sell asset lots\n"
                                           f"Где, asset -- название актива, lots -- кол-во лотов (лот = 10 шт.)"
                                           )


def sell_assets(order: Order) -> bool:
    """Создать заявку на покупку акций"""
    lots = get_lots(order.user_id, order.asset_name)
    if broker.check_assets(order, lots):
        broker.create_sell_order(order)
        exchange.close_the_deal(order)
    else:
        raise exceptions.BrokerException(f"Не хватает акций.\n"
                                         f"Купите пакеты акций: /buy {order.asset_name} {order.lots}")
    return True


def buy_assets(order: Order) -> bool:
    """Создать заявку на покупку акций"""
    balance = get_balance(order.user_id)
    if broker.check_balance(order, balance):
        broker.create_buy_order(order)
        exchange.close_the_deal(order)
    else:
        raise exceptions.BrokerException(f"Не хватает средств.\n"
                                         f"Пополните баланс командой: /change_balance {order.price}")
    return True


def get_my_orders(user_id: int) -> str:
    """получить все заявки от профиля по id"""
    my_orders = db_requests.fetchall_by_id("reg_orders", ["type", "asset", "price", "status", "date"],
                                           user_id)
    message = ''
    if len(my_orders) == 0:
        message = 'У профиля нет заявок'
        return message
    else:
        for row in my_orders:
            for key in row.keys():
                message += str(row[key]) + ' '
            message += '\n'
        return message
