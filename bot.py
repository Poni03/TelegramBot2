import time 
import datetime
import logging
import config
import texts
import asyncio
import os
import re
import g4f
import nest_asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.utils import executor
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.deep_linking import get_start_link, decode_payload
from aiogram.dispatcher import Dispatcher
from aiogram.utils.markdown import hbold, hunderline, hcode, hlink

import markup as nav
from bot_db import Database
from bot_referral import Referr

import json
import uuid
from yookassa import Configuration as yooConfig
from yookassa import Payment as yooPayment

logging.basicConfig(level=logging.INFO)

yooConfig.account_id = config.SHOP_ID
yooConfig.secret_key = config.SHOP_API_TOKEN


bot = Bot(token=config.TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

db = Database(config.DB_FILE)

PRICE_1 = types.LabeledPrice(label='Подписка на 1 месяц', amount=199)
PRICE_3 = types.LabeledPrice(label='Подписка на 3 месяца', amount=477)
REFFERAL_PRICE_1 = types.LabeledPrice(label='Подписка на 1 месяц (10% скидка)', amount=179)
REFFERAL_PRICE_3 = types.LabeledPrice(label='Подписка на 3 месяца (10% скидка)', amount=429)
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
            await bot.send_message(message.chat.id, "Вы уже зарегистрированы!", reply_markup=nav.mainDMD)

        else:
            decrypted_link = Referr.decrypt_referral_link(message.text)
            referral_id = str(decrypted_link[7:])

            await message.answer(texts.TEXT_START)

            if str(referral_id) != '':
                if int(referral_id) != int(message.from_user.id):
                    await bot.send_message(referral_id, "По вашей ссылке зарегистрировался новый пользователь", reply_markup=nav.mainDMD)
                else:
                    referral_id = None
                    await message.answer(',Нельзя регистрироваться по собственной реферальной ссылке!', reply_markup=nav.mainDMD)

            db.add_user(message.from_user.id, referral_id, message.from_user.username)
            db.add_date_sub(message.from_user.id, config.DAYS_FREE_USE)

    except Exception as e:
        logging.error(f'Error in start_cmd: {e}')

@dp.message_handler(commands="help")
@dp.message_handler(lambda message: message.text and 'помощь' in message.text.lower())
async def instruction_info(message: types.Message) -> None:
    await message.answer(f"{texts.TEXT_INSTRUCTION}")

@dp.message_handler(commands="newtopic")
@dp.message_handler(lambda message: message.text and 'новая тема' in message.text.lower())
async def new_topic(message: types.Message) -> None:
    try:
        user_id = message.from_user.id
        messages[user_id] = []
        messages[user_id].append({"role": "user", "content": "твоя роль писателя ответы на русском языке не более 150 слов"})

        await message.answer('Начинаем новую тему!', parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Error in new_topic_cmd: {e}')

@dp.message_handler(commands=("share"))
async def give_info(message: types.Message) -> None:
    encrypted_link = Referr.encrypt_referral_link(message.from_user.id)
    info = await bot.get_me()
    name = info.username
    share_text = f"https://t.me/{name}?start={encrypted_link}"
    share_inline = InlineKeyboardMarkup(row_width=2)

    inline_share = InlineKeyboardButton(text="Поделиться реферальной ссылкой", url=f'https://t.me/share/url?url={share_text}')
    share_inline.add(inline_share)
    await message.answer(texts.TEXT_REFERRAL, reply_markup=share_inline)

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
    line1 = f"Дата окончания: <b>{date_string}</b>"
    line2 = f"Ваша реферальная сcылка:"
    line3 = f"Кол-во рефералов: <b>{db.count_referral(message.from_user.id)}</b>"
    line4 = f"Кол-во запросов: <b>{db.get_counter_msg(message.from_user.id)}</b>"
    share_inline = InlineKeyboardMarkup(row_width=2)

    inline_share = InlineKeyboardButton(text="Поделиться реферальной ссылкой", url=f'https://t.me/share/url?url={share_text}')
    share_inline.add(inline_share)
    await message.answer(f"{line1}\n{line2}\n{hcode(share_text)}\n{line3}\n{line4}", reply_markup=share_inline)

@dp.message_handler(commands="subscribe")
@dp.message_handler(lambda message: message.text and 'оформить подписку' in message.text.lower())
async def subscribe_handler(message: types.Message):
    await message.answer(f"Выберите и оформите подписку!", reply_markup=nav.sub_inline_murk)

@dp.message_handler(content_types="text")
async def send(message: types.Message):
        user_message = message.text
        user_id = message.from_user.id
        user_name = message.from_user.username

        if not db.get_date_status(user_id):
            await message.reply(f"Закончилось время подписки. Пожалуйста, оформите подписку!", reply_markup=nav.sub_inline_murk)
            return

        processing_msg = await message.answer('⏳ Идет обработка данных...')
        await bot.send_chat_action(message.chat.id, action="typing")
        if user_id not in messages:
            messages[user_id] = []
            messages[user_id].append({"role":"user", "content":"твоя роль писателя ответы на русском языке не более 150 слов"})

        messages[user_id].append({"role":"user", "content": user_message})
        try:
            chatgpt_response = g4f.ChatCompletion.create(model="gpt-3.5-turbo", provider=g4f.Provider.DeepAi, messages=messages[user_id])
            #print(chatgpt_response)
            if not chatgpt_response:
                raise Exception("manyrequestempty")
            if chatgpt_response == "Unable to fetch the response, Please try again.":
                raise Exception("manyrequest")
            # Add the bot's response to the user's message history
            messages[user_id].append({"role":"assistant", "content": chatgpt_response})
            await message.answer(chatgpt_response)
            await db.increment_counter_msg(user_id)
        except Exception as ex:
            logging.error(f'Error in chat: {ex}')
            if ex == "manyrequest":
                await message.answer('Слишком много запросов, подождите некоторое время и попробуйте снова. Либо установите ограничение текста', parse_mode='Markdown')
            else:
                await message.answer(f'Непредвиденная ошибка, подождите некоторое время и попробуйте снова {ex}', parse_mode='Markdown')

        await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
        await db.set_last_active_time(user_id)        

async def set_payment_success(user_id:int, payment, payload:str):
    try:
        answer = f"Платеж на сумму {payment['amount']['value']} {payment['amount']['currency']} прошел успешно!!!"
        add_days = config.DAYS_ADD_TO_PAYMENT
        if payload == "moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 30 дней!"
            add_days = 30
        elif payload == "three_moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 90 дней!"
            add_days = 90
        elif payload == "ref_moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 30 дней со скидкой!"
            add_days = 30
        elif payload == "ref_three_moth_sub":
            answer = answer + "\n Подзравляю вам выдана подписка на 90 дней со скидкой!"
            add_days = 90

        db.add_date_sub(user_id, add_days)
        await bot.send_message(user_id, answer)

        referral_id = db.get_referral_id(user_id)
        if referral_id is not None:
            db.add_date_sub(referral_id, config.DAYS_ADD_FOR_REFFERAL)
            await bot.send_message(referral_id, f'Ваша подписка продлена на {config.DAYS_ADD_FOR_REFFERAL} дней, по Вашей реферальной ссылке зачислены средства')

        await db.set_first_pay_status(user_id)
    except Exception as ex:
        logging.error(f'Error in payment: {ex}')

@dp.callback_query_handler(lambda c: c.data.startswith('submonth_'))
async def handle_callback_query(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split("_")[1]
    try:        
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

        price_str = str(price.amount)+".00"
        info = await bot.get_me()
        name = info.username
        share_url = f"https://t.me/{name}"

        idempotence_key = str(uuid.uuid4())
        payment = yooPayment.create({
            "amount": {
                "value": price_str,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": share_url
            },
            "description": description,
            "capture": True
        }, idempotence_key)

        payment_data = json.loads(payment.json())

        payment_id = payment_data['id']
        payment_url = (payment_data['confirmation'])['confirmation_url']

        description += "\nСсылка на оплату действует в течении одного часа, после чего он будет отменен."

        payment_button = InlineKeyboardButton(f"Заплатить {price_str} р.", url=payment_url)
        await bot.send_message(user_id, description ,reply_markup=InlineKeyboardMarkup(row_width=1).add(payment_button))

        db.add_payment(user_id, payment_id, payment_data['status'], price_str, payload)

        #это сразу проверка с capture true
        if payment_data['status'] == 'succeeded':
            await set_payment_success(user_id, payment_data, payload)
        elif payment_data['status'] == 'canceled':
            date_create_str = datetime.datetime.strptime(payment_data['created_at'][:19], "%Y-%m-%dT%H:%M:%S").strftime('%d-%m-%Y %H:%M')
            await bot.send_message(user_id, f"Ваш платеж от {date_create_str} отменён, либо прошло время действия ссылки", reply_markup=nav.sub_inline_murk)

    except Exception as e:
        await bot.send_message(user_id, "Не сформировался чек. попробуйте позже.")
        logging.error(f'Error in subscribe: {e}')

async def check_payment(timedata):
    list_payments = db.get_payments_for_status("pending")
    if list_payments is not None:
        for payment_row in list_payments:
            payment_id = payment_row[0]
            user_id = payment_row[1]
            payload = payment_row[2]
            payment = json.loads((yooPayment.find_one(payment_id)).json())

            if payment['status'] != 'pending':
                db.update_payment_status(payment_id, payment['status'])
                if payment['status'] == 'succeeded':
                    await set_payment_success(user_id, payment, payload)
                elif payment['status'] == 'canceled':
                    date_create_str = datetime.datetime.strptime(payment['created_at'][:19], "%Y-%m-%dT%H:%M:%S").strftime('%d-%m-%Y %H:%M')
                    await bot.send_message(user_id, f"Ваш платеж от {date_create_str} отменён, либо прошло время действия ссылки", reply_markup=nav.sub_inline_murk)

            await asyncio.sleep(7) #5 секунд ожидания каждого запроса, чтобы не заткнуть АПИ

        list_payments = db.get_payments_for_status("waiting_for_capture")
        for payment_row in list_payments:
            payment_id = payment_row[0]
            user_id = payment_row[1]
            payload = payment_row[2]
            payment = json.loads((yooPayment.find_one(payment_id)).json())
            if payment['status'] != 'waiting_for_capture':
                db.update_payment_status(payment_id, payment['status'])
                if payment['status'] == 'succeeded':
                    await set_payment_success(user_id, payment, payload)
                elif payment['status'] == 'canceled':
                    date_create_str = datetime.datetime.strptime(payment['created_at'][:19], "%Y-%m-%dT%H:%M:%S").strftime('%d-%m-%Y %H:%M')
                    await bot.send_message(user_id, f"Ваш платеж от {date_create_str} отменён, либо прошло время действия ссылки", reply_markup=nav.sub_inline_murk)

            await asyncio.sleep(7) #5 секунд ожидания каждого запроса, чтобы не заткнуть АПИ

    await asyncio.sleep(timedata) #ждем

async def reminder_send(timedata):
    list_reminders = db.get_users_reminder_days(config.DAYS_REMINDER)
    if list_reminders is not None:
        for reminder_row in list_reminders:
            user_id = reminder_row[0]
            await bot.send_message(user_id, texts.REMINDER)
            await db.set_last_active_time(user_id)

    await asyncio.sleep(timedata) #ждем

async def setup_bot_commands(dp):
    bot_commands = [
        types.BotCommand("/newtopic", "Новая тема"),
        types.BotCommand("/share", "Реферальная программа"),
        types.BotCommand("/subscribe", "Оплата подписки"),
        types.BotCommand("/help", "Помощь"),
    ]
    await dp.bot.set_my_commands(bot_commands)

def init():
    db.update_fields()

async def main():
    while True:
        await check_payment(10)
        await reminder_send(10)

if __name__ == '__main__':
    init()
    nest_asyncio.apply()
    loopbot=asyncio.get_event_loop()
    loopbot.create_task(main())
    executor.start_polling(dp, skip_updates = True, on_startup=setup_bot_commands)
