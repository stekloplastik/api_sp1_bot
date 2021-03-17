import os
import time
import logging

import requests
from telegram import Bot
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)

logger = logging.getLogger('homework')
handler = RotatingFileHandler('logs.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL_API = "https://praktikum.yandex.ru/api/user_api/homework_statuses/"


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'reviewing':
        verdict = 'Работу проверяют'
    elif homework_status == 'approved':
        verdict = ('Ревьюеру всё понравилось, можно '
                   'приступать к следующему уроку.')
    else:
        logger.error('Неизвестный статус домашнего задания')
        return f'{homework_status} - эээ...(пускает слюни)'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    current_timestamp = int(time.time()) if current_timestamp is None \
        else current_timestamp
    params = {
        'from_date': current_timestamp,
    }
    try:
        homework_statuses = requests.get(URL_API, headers=headers,
                                         params=params)
        return homework_statuses.json()
    except requests.RequestException as e:
        logger.error(f'Не удалось получить статус домашней работы. Ошибка {e}')


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.debug(msg='Поехали')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp,
            )
            time.sleep(300)

        except Exception as e:
            logger.error(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
