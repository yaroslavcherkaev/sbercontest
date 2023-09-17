"""модуль для работы с БД"""
import os
from typing import Dict, List, Tuple

import sqlite3

import exceptions
from custom_types import Order

conn = sqlite3.connect(os.path.join("db", "sbercontest.db"))
cursor = conn.cursor()


def insert(table: str, column_values: Dict):
    columns = ', '.join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join("?" * len(column_values.keys()))
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def select(table: str, columns: List[str], user_id: int) -> Dict:
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table} where user_id={user_id}")
    rows = cursor.fetchall()
    dict_row = {}
    for row in rows:
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
    return dict_row


def select_active_offer(order: Order) -> Order:
    if order.order_type == 'BUY':
        necessary_type = 'SELL'
    else:
        necessary_type = 'BUY'

    cursor.execute(f"SELECT * FROM reg_orders WHERE type = '{necessary_type}' AND asset = '{order.asset_name}' "
                   f"AND lots = {order.lots} AND status = 'ACTIVE' AND user_id <> {order.user_id} "
                   f"ORDER BY date DESC ")
    rows = cursor.fetchall()
    if len(rows) != 0:
        deal_with = rows[0]
        offer = Order(order_id=deal_with[0], user_id=deal_with[1],
                      order_type=deal_with[2], asset_name=deal_with[3],
                      lots=deal_with[4], price=deal_with[5])
        return offer
    else:
        raise exceptions.ExchangerException("Нет открытых заявок. Сделка будет совершена с эмитентом")


def update_asset_pcs(user_id: int, asset_name: str, new_value: int) -> None:
    cursor.execute(f"UPDATE 'users' SET {asset_name} = {new_value} WHERE user_id={user_id}")
    conn.commit()


def update_status(order_id: str) -> None:
    cursor.execute(f"UPDATE 'reg_orders' SET status = 'CLOSED' WHERE order_id='{order_id}'")
    conn.commit()


def update_balance(user_id: int, new_value: str) -> None:
    cursor.execute(f"UPDATE 'users' SET balance = {new_value} WHERE user_id={user_id}")
    conn.commit()


def fetchall(table: str, columns: List[str]) -> List[Dict]:
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table}")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def fetchall_by_id(table: str, columns: List[str], user_id: int) -> List[Dict]:
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table} WHERE user_id = {user_id}")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def fetchall_by_id_and_asset(table: str, columns: List[str], user_id: int, asset_name: str) -> List[Dict]:
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table} WHERE user_id = {user_id} AND asset = '{asset_name}'")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def delete(table: str, row_id: int) -> None:
    row_id = int(row_id)
    cursor.execute(f"delete from {table} where id={row_id}")
    conn.commit()


def get_cursor():
    return cursor


def _init_db():
    """Инициализирует БД"""
    with open("createdb.sql", "r") as f:
        sql = f.read()
        cursor.executescript(sql)
        conn.commit()


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='users'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()


check_db_exists()
