"""Кастомные исключения, генерируемые приложением"""


class NotCorrectMessage(Exception):
    """Некорректное сообщение в бот, которое не удалось распарсить"""
    pass


class BrokerException(Exception):
    """Используется для обработки исключений при проверке баланса и кол-ва акций
    перед оформлением заявки"""
    pass


class ExchangerException(Exception):
    """Используется для обработки исключений во время совершения сделок"""
    pass