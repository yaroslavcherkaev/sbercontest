"""Серверная часть бота, содержит команды для симуляции торговли на бирже"""
from os import getenv
import sys
import asyncio
import logging
import uuid
from decimal import Decimal, InvalidOperation

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command

from custom_types import AssetPrice, Order
import profile
import exceptions

API_TOKEN = getenv("TELEGRAM_API_TOKEN")

COMMANDS_MESSAGE = f"Посмотреть баланс: /balance\n" \
                   f"Посмотреть рынок: /assets\n" \
                   f"Пополнить баланс: /change_balance 100000\n" \
                   f"Посмотреть портфель: /portfolio\n" \
                   f"Посмотреть команды:  /help\n" \
                   f"Посмотреть заявки: /orders\n" \
                   f"Купить пакет акций: /buy SBER 1\n" \
                   f"Продать пакет акций: /sell VTBR 1\n" \


bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def send_welcome(message: types.Message) -> None:
    """онбординг пользователя"""
    user_id = int(message.from_user.id)
    profile.onboarding(user_id)
    await message.reply(
        f"Бот для конкурса красоты кода\n\n"
        f"Симуляция торговли на фондовом рынке\n"
        f"--------\n"
        f"{COMMANDS_MESSAGE}",
        reply=False)


@dp.message(Command("help"))
async def send_help(message: types.Message) -> None:
    """отправить доступные команды бота"""
    await message.reply(
        f"Бот для конкурса красоты кода\n\n"
        f"Симуляция торговли на фондовом рынке\n"
        f"--------\n"
        f"{COMMANDS_MESSAGE}",
        reply=False)


@dp.message(Command("assets"))
async def send_assets(message: types.Message) -> None:
    """отправить акции, которые можно купить"""
    available_assets = ""
    for asset in AssetPrice:
        name = str(asset.name)
        if name == "ASSETS":
            available_assets += "Доступные акции:\n"
        else:
            value = round(asset.value, 4)
            available_assets += name + ": " + str(value) + "\n"
    await message.reply(
        f"{available_assets}"
        f"--------\n"
        f"{COMMANDS_MESSAGE}",
        reply=False)


@dp.message(Command("balance"))
async def send_balance(message: types.Message) -> None:
    user_id = int(message.from_user.id)
    balance = profile.get_balance(user_id)
    await message.reply(
        f"Ваш баланс: {balance}\n"
        f"--------\n"
        f"{COMMANDS_MESSAGE}",
        reply=False)


@dp.message(lambda message: message.text.startswith('/change_balance'))
async def change_balance(message: types.Message) -> None:
    """пополнить баланс профиля"""
    user_id = int(message.from_user.id)
    try:
        value = Decimal(message.text[15:])
        if (value <= 0) or (value > 500000):
            raise exceptions.NotCorrectMessage(f"Введите положительное число больше нуля\n"
                                               f"За раз можно пополнить не более чем на 500000")
        else:
            balance = profile.change_balance(user_id, value)
            await message.reply(
                f"Ваш баланс: {balance}\n"
                f"--------\n"
                f"{COMMANDS_MESSAGE}",
                reply=False)
    except InvalidOperation:
        await message.reply(
            f"Неверный формат\n"
            f"--------\n"
            f"{COMMANDS_MESSAGE}",
            reply=False)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))


@dp.message(Command("portfolio"))
async def send_portfolio(message: types.Message) -> None:
    """отправить статистику портфеля"""
    user_id = int(message.from_user.id)
    portfolio = profile.get_portfolio(user_id)
    str_portfolio = ""
    for key in portfolio.keys():
        if key != 'value':
            str_portfolio += f"{key}: {portfolio[key]}\n"
    str_portfolio += f"Цена портфеля: {portfolio['value']}\n"
    await message.reply(
        f"{str_portfolio}\n"
        f"--------\n"
        f"{COMMANDS_MESSAGE}",
        reply=False)


@dp.message(lambda message: message.text.startswith('/buy'))
async def buy_asset(message: types.Message) -> None:
    """ Функция отправки заявки на покупку акций по рыночной цене"""
    user_id = int(message.from_user.id)
    try:
        parsed_order = profile.parse_order(message.text[4:])
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    order_id = str(uuid.uuid4())
    pcs = parsed_order['lots'] * AssetPrice.lot_weight.value
    price = pcs * AssetPrice[parsed_order['asset']].value
    order = Order(order_id=order_id, user_id=user_id,
                  order_type='BUY', asset_name=parsed_order['asset'],
                  lots=parsed_order['lots'], price=price)
    try:
        profile.buy_assets(order)
        await message.reply(
            f"Заявка на покупку принята\n"
            f"--------\n"
            f"{COMMANDS_MESSAGE}",
            reply=False)
    except exceptions.BrokerException as e:
        await message.answer(str(e))
        return


@dp.message(lambda message: message.text.startswith('/sell'))
async def sell_asset(message: types.Message) -> None:
    """ Функция отправки заявки на продажу акций по рыночной цене"""
    user_id = int(message.from_user.id)
    try:
        parsed_order = profile.parse_order(message.text[5:])
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    order_id = str(uuid.uuid4())
    pcs = parsed_order['lots'] * AssetPrice.lot_weight.value
    price = pcs * AssetPrice[parsed_order['asset']].value
    order = Order(order_id=order_id, user_id=user_id,
                  order_type='SELL', asset_name=parsed_order['asset'],
                  lots=parsed_order['lots'], price=price)
    try:
        profile.sell_assets(order)
        await message.reply(
            f"Заявка на продажу принята\n"
            f"--------\n"
            f"{COMMANDS_MESSAGE}",
            reply=False)
    except exceptions.BrokerException as e:
        await message.answer(str(e))
        return


@dp.message(lambda message: message.text.startswith('/orders'))
async def send_orders(message: types.Message) -> None:
    """Функция отправки активных заявок пользователя"""
    user_id = int(message.from_user.id)
    orders = profile.get_my_orders(user_id)
    await message.answer(orders)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
