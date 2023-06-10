import time 
import datetime
import logging
import config
import asyncio
import os
import you

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.utils import executor
from aiogram.types import Message
from aiogram.utils.deep_linking import get_start_link, decode_payload
from aiogram.dispatcher import Dispatcher

import markup as nav
from bot_db import Database
from bot_referral import Referr

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)
# database for local use
db = Database('db/db.db')
# database for docker container docker-compose up -d
# db = Database('/root/db.db')

async def setup_bot_commands(dp):
    bot_commands = [
        types.BotCommand("/newtopic", "Новая тема"),
        types.BotCommand("/myprofile", "Профиль"),
        types.BotCommand("/instruction", "Инструкция"),
        types.BotCommand("/referral", "Реферальная программа"),
        types.BotCommand("/instruction", "Инструкция"),
        types.BotCommand("/subscribe", "Оплата подписки"),
    ]
    await dp.bot.set_my_commands(bot_commands)


PRICE_1 = types.LabeledPrice(label='Подписка на 1 месяц', amount=199*100)
PRICE_3 = types.LabeledPrice(label='Подписка на 3 месяца', amount=477*100)
REFFERAL_PRICE_1 = types.LabeledPrice(label='Подписка на 1 месяц (10% скидка)', amount=179*100)
REFFERAL_PRICE_3 = types.LabeledPrice(label='Подписка на 3 месяца (10% скидка)', amount=429*100)
user_messages = {}
messages = {}

async def auto_delete_message(chat_id: int, message_id: int):
    """Функция для удаления сообщения через 3 секунд"""
    await asyncio.sleep(3)
    await bot.delete_message(chat_id, message_id)

def date_sub_day(get_time):
    data_now = int(time.time())
    data_midle = int(get_time) - data_now

    if data_midle <= 0:
        return False
    else:
        dt = str(datetime.timedelta(seconds=data_midle))
        dt = dt.replace('days', 'дней')
        dt = dt.replace('day', 'день')
        return dt


@dp.message_handler(commands="start")
async def start_message(message: types.Message) -> None:
    """welcome message."""
    try:
        exist = await db.user_exists(message.from_user.id)
        if exist:
            await bot.send_message(message.chat.id, "Вы уже зарегистрированы!")

        else:
            decrypted_link = Referr.decrypt_referral_link(message.text)
            referral_id = str(decrypted_link[7:])

            await message.answer(config.TEXT_START)

            if str(referral_id) != '':
                if int(referral_id) != int(message.from_user.id):
                    await bot.send_message(referral_id, "По вашей ссылке зарегистрировался новый пользователь")
                else:
                    referral_id = None
                    await message.answer('Нельзя регистрироваться по собственной реферальной ссылке!')

            db.add_user(message.from_user.id, referral_id, message.from_user.username)
            db.add_date_sub(message.from_user.id, config.DAYS_FREE_USE)

    except Exception as e:
        logging.error(f'Error in start_cmd: {e}')
    
@dp.message_handler(commands=("instruction"))
async def instruction_info(message: types.Message) -> None:
    await message.answer(config.TEXT_INSTRUCTION)
@dp.message_handler(commands=("about"))
async def give_info(message: types.Message) -> None:
    await message.answer(config.TEXT_ABOUT)
@dp.message_handler(commands=("referral"))
async def give_info(message: types.Message) -> None:
    await message.answer(config.TEXT_REFERRAL)


@dp.message_handler(commands="newtopic")
@dp.message_handler(lambda message: message.text and 'новая тема' in message.text.lower())
async def new_topic(message: types.Message) -> None:
    try:
        user_id = message.from_user.id
        messages[user_id] = []
        messages[user_id].append({"question": "изначально ответы на русском языке не более 150 слов", "answer": "конечно"})

        await message.answer('Начинаем новую тему!', parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Error in new_topic_cmd: {e}')

@dp.message_handler(commands="myprofile")
@dp.message_handler(lambda message: message.text and 'профиль' in message.text.lower())
async def profile_handler(message: types.Message):
    date_string = ''
    user_sub = False
    date_seconds = db.get_date(message.from_user.id)
    if date_seconds != None:
        date_string = datetime.datetime.utcfromtimestamp(date_seconds).strftime('%d-%m-%Y %H:%M')
        user_sub = date_sub_day(date_seconds)

    if user_sub == False:
        user_sub = "Нет"
    encrypted_link = Referr.encrypt_referral_link(message.from_user.id)
    info = await bot.get_me()
    name = info.username
    share_text = f"https://t.me/{name}?start={encrypted_link}"
    await message.answer(f'Дата окончания: {date_string}\nID: {message.from_user.id}\nВаша реферальная сcылка:\n{share_text}\nКол-во рефералов:{db.count_referral(message.from_user.id)}')


@dp.callback_query_handler(lambda c: c.data.startswith('submonth_'))
async def handle_callback_query(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        action = callback.data.split("_")[1]
        # set parameters
        add_days = 30
        price = PRICE_1
        start_parameter = "one-month-subscription"
        payload = "moth_sub"
        if action == "3":
            add_days = 90
            price = PRICE_3
            payload = "three_moth_sub"
            start_parameter = "three-month-subscription"

        description = f"Активация подписки на бота на {add_days} дней"
        
        if db.get_referral_discount(user_id):
            description = description + " скидка за реферальную систему 10%"
            price = REFFERAL_PRICE_1
            payload = "ref_moth_sub"
            if action == "3":
                price = REFFERAL_PRICE_3
                payload = "ref_three_moth_sub"

        await bot.send_invoice(callback.message.chat.id,
            title="Подписка на бота",
            description=description,
            provider_token=config.PAYMENTS_TOKEN,
            currency="rub",
            photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
            photo_width=416,
            photo_height=234,
            photo_size=416,
            is_flexible=False,
            prices=[price],
            start_parameter=start_parameter,
            payload=payload)
    except Exception as e:
        logging.error(f'Error in subscribe: {e}')


@dp.message_handler(commands="subscribe")
@dp.message_handler(lambda message: message.text and 'оформить подписку' in message.text.lower())
async def subscribe_handler(message: types.Message):
    await message.answer(f"Выберите и оформите подписку!", reply_markup=nav.sub_inline_murk)

@dp.message_handler(content_types="text")
async def send(message: types.Message):
    try:
        user_message = message.text
        user_id = message.from_user.id
        user_name = message.from_user.username

        if(db.get_date_status(user_id)):
            processing_msg = await message.answer('⏳ Идет обработка данных...')
            await bot.send_chat_action(message.chat.id, action="typing")
            # asyncio.ensure_future(auto_delete_message(message.chat.id, processing_msg.message_id))
            if user_id not in messages:
                messages[user_id] = []
                messages[user_id].append({"question": "изначально ответы на русском языке не более 150 слов", "answer": "конечно"})

            chatgpt_response = you.Completion.create(prompt=user_message, chat=messages[user_id])
            chatgpt_response_text = chatgpt_response.text.replace("\\/", "/").encode().decode('unicode_escape')
            # Add the bot's response to the user's message history
            messages[user_id].append({"question": user_message, "answer": chatgpt_response_text})

            await message.answer(chatgpt_response_text)

            await db.increment_counter_msg(user_id)
            await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)

        else:
            await message.answer(f"Закончилось время подписки. Пожалуйста, оформите подписку!", reply_markup=nav.sub_inline_murk)

    except Exception as ex:
        # If an error occurs, try starting a new topic
        if 'processing_msg' in values():
            await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
        print(ex)
        if ex == "context_length_exceeded":
            await message.reply('У бота закончилась память, пересоздаю диалог', parse_mode='Markdown')
            await new_topic(message)
            await send(message)
        else:
            await message.reply('У бота возникла ошибка, подождите некоторое время и попробуйте снова. Либо установите ограничение текста', parse_mode='Markdown')


# pre checkout  (must be answered in 10 seconds)
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


# successful payment
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    try:
        answer = f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!"
        add_days = config.DAYS_ADD_TO_PAYMENT
        if message.successful_payment.invoice_payload == "moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 30 дней!"
            add_days = 30
        elif message.successful_payment.invoice_payload == "three_moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 90 дней!"
            add_days = 90
        elif message.successful_payment.invoice_payload == "ref_moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 30 дней со скидкой!"
            add_days = 30
        elif message.successful_payment.invoice_payload == "ref_three_moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 90 дней со скидкой!"
            add_days = 90

        db.add_date_sub(message.from_user.id, add_days)
        await message.answer(answer)

        referral_id = db.get_referral_id(message.from_user.id)
        if referral_id is not None:
            db.add_date_sub(referral_id, config.DAYS_ADD_FOR_REFFERAL)
            await bot.send_message(referral_id, f'Ваша подписка продлена на {config.DAYS_ADD_FOR_REFFERAL} дней, по Вашей реферальной ссылке зачислены средства')

        db.set_first_pay_status(message.from_user.id)

    except Exception as e:
        logging.error(f'Error in payment: {e}')

if __name__ == '__main__':
	executor.start_polling(dp, skip_updates = True, on_startup=setup_bot_commands)