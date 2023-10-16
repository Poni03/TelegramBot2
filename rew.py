import logging
import g4f
import os
import re
import time 
import datetime
import asyncio

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext, InlineQueryHandler, CallbackQueryHandler

import config
import texts
import rew_markup as nav
from bot_db import Database
from bot_referral import Referr

import json
import uuid
from yookassa import Configuration as yooConfig
from yookassa import Payment as yooPayment

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#parse_mode=types.ParseMode.HTML
db = Database(config.DB_FILE)
#bot = telegram.Bot(token=config.TOKEN)

PRICE_1 = LabeledPrice(label='Подписка на 1 месяц', amount=199)
PRICE_3 = LabeledPrice(label='Подписка на 3 месяца', amount=477)
REFFERAL_PRICE_1 = LabeledPrice(label='Подписка на 1 месяц (10% скидка)', amount=179)
REFFERAL_PRICE_3 = LabeledPrice(label='Подписка на 3 месяца (10% скидка)', amount=429)
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


"""welcome message."""
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        exist = await db.user_exists(update.message.from_user.id)
        if exist:
            await context.bot.send_message(update.message.chat.id, "Вы уже зарегистрированы!", reply_markup=nav.keyboard_button)

        else:
            decrypted_link = Referr.decrypt_referral_link(update.message.text)
            referral_id = str(decrypted_link[7:])

            await context.bot.send_message(update.message.chat.id, texts.TEXT_START)

            if str(referral_id) != '':
                if int(referral_id) != int(update.message.from_user.id):
                    await context.bot.send_message(referral_id, "По вашей ссылке зарегистрировался новый пользователь", reply_markup=nav.keyboard_button)
                else:
                    referral_id = None
                    await context.bot.send_message(update.message.chat.id, ',Нельзя регистрироваться по собственной реферальной ссылке!', reply_markup=nav.keyboard_button)

            db.add_user(update.message.from_user.id, referral_id, update.message.from_user.username)
            db.add_date_sub(update.message.from_user.id, config.DAYS_FREE_USE)

    except Exception as e:
        logging.error(f'Error in start_cmd: {e}')


async def give_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    encrypted_link = Referr.encrypt_referral_link(update.message.from_user.id)
    info = await context.bot.get_me()
    name = info.username
    share_text = f"https://t.me/{name}?start={encrypted_link}"

    share_inline = [

        [

            InlineKeyboardButton(text="Поделиться реферальной ссылкой", url=f'https://t.me/share/url?url={share_text}')

        ]

    ]

    share_inline = InlineKeyboardMarkup(share_inline)
    #print(share_inline)
    await context.bot.send_message(update.message.chat.id, texts.TEXT_REFERRAL, reply_markup=share_inline, parse_mode='html')

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    date_string = ''
    user_sub = False
    date_seconds = db.get_date(update.message.from_user.id)
    if date_seconds != None:
        date_string = datetime.datetime.utcfromtimestamp(date_seconds).strftime('%d-%m-%Y %H:%M')
        user_sub = date_sub_day(date_seconds)

    if user_sub == False:
        user_sub = "Нет"
    encrypted_link = Referr.encrypt_referral_link(update.message.from_user.id)
    info = await context.bot.get_me()
    name = info.username
    share_text = f"https://t.me/{name}?start={encrypted_link}"
    line1 = f"Дата окончания: <b>{date_string}</b>"
    line2 = f"Ваша реферальная сcылка:"
    line3 = f"Кол-во рефералов: <b>{db.count_referral(update.message.from_user.id)}</b>"
    line4 = f"Кол-во запросов: <b>{db.get_counter_msg(update.message.from_user.id)}</b>"
    share_inline = [

        [

            InlineKeyboardButton(text="Поделиться реферальной ссылкой", url=f'https://t.me/share/url?url={share_text}')

        ]

    ]

    share_inline = InlineKeyboardMarkup(share_inline)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{line1}\n{line2}\n{share_text}\n{line3}\n{line4}", reply_markup=share_inline, parse_mode='html')

async def instruction_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{texts.TEXT_INSTRUCTION}", parse_mode='html')


async def new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_id = update.effective_chat.id
        messages[user_id] = []
        messages[user_id].append({"role": "user", "content": "твоя роль писателя ответы на русском языке не более 150 слов"})

        await context.bot.send_message(chat_id=update.effective_chat.id, text='Начинаем новую тему!', parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Error in new_topic_cmd: {e}')

async def send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        user_id = update.effective_chat.id
        user_name = update.effective_user.full_name

        if user_message.lower() in "новая тема":
            await new_topic(update, context)
            return

        if user_message.lower() in "👤 профиль":
            await profile_handler(update, context)
            return

        if not db.get_date_status(user_id):
            await update.message.reply_text(f"Закончилось время подписки. Пожалуйста, оформите подписку!", reply_markup=nav.inline_payments_choice)
            return

        processing_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text='⏳ Идет обработка данных...')
        await context.bot.send_chat_action(update.message.chat.id, action="typing")
        if user_id not in messages:
            messages[user_id] = []
            messages[user_id].append({"role":"user", "content":"твоя роль писателя ответы на русском языке не более 150 слов"})

        messages[user_id].append({"role":"user", "content": user_message})
        try:
            chatgpt_response = g4f.ChatCompletion.create(model="gpt-3.5-turbo", provider=g4f.Provider.Bing, messages=messages[user_id])
            #print(chatgpt_response)
            if not chatgpt_response:
                raise Exception("manyrequestempty")
            if chatgpt_response == "Unable to fetch the response, Please try again.":
                raise Exception("manyrequest")
            # Add the bot's response to the user's message history
            messages[user_id].append({"role":"assistant", "content": chatgpt_response})
            await context.bot.send_message(chat_id=update.effective_chat.id, text=chatgpt_response)
            await db.increment_counter_msg(user_id)
        except Exception as ex:
            logging.error(f'Error in chat: {ex}')
            if ex == "manyrequest":
                await context.bot.send_message(chat_id=update.effective_chat.id, text='Слишком много запросов, подождите некоторое время и попробуйте снова. Либо установите ограничение текста', parse_mode='Markdown')
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Непредвиденная ошибка, подождите некоторое время и попробуйте снова {ex}', parse_mode='Markdown')

        await context.bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
        await db.set_last_active_time(user_id)

async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Выберите и оформите подписку!", reply_markup=nav.inline_payments_choice)

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
        await context.bot.send_message(user_id, answer)

        referral_id = db.get_referral_id(user_id)
        if referral_id is not None:
            db.add_date_sub(referral_id, config.DAYS_ADD_FOR_REFFERAL)
            await context.bot.send_message(referral_id, f'Ваша подписка продлена на {config.DAYS_ADD_FOR_REFFERAL} дней, по Вашей реферальной ссылке зачислены средства')

        await db.set_first_pay_status(user_id)
    except Exception as ex:
        logging.error(f'Error in payment: {ex}')


async def handler_callback_query(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    action = update.callback_query.data.split("_")[1]
    #print(action)
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
        info = await context.bot.get_me()
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
        await context.bot.send_message(user_id, description ,reply_markup=InlineKeyboardMarkup(row_width=1).add(payment_button))

        db.add_payment(user_id, payment_id, payment_data['status'], price_str, payload)

        #это сразу проверка с capture true
        if payment_data['status'] == 'succeeded':
            await set_payment_success(user_id, payment_data, payload)
        elif payment_data['status'] == 'canceled':
            date_create_str = datetime.datetime.strptime(payment_data['created_at'][:19], "%Y-%m-%dT%H:%M:%S").strftime('%d-%m-%Y %H:%M')
            await context.bot.send_message(user_id, f"Ваш платеж от {date_create_str} отменён, либо прошло время действия ссылки", reply_markup=nav.sub_inline_murk)

    except Exception as e:
        await context.bot.send_message(user_id, "Не сформировался чек. попробуйте позже.")
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
                    await update.bot.send_message(user_id, f"Ваш платеж от {date_create_str} отменён, либо прошло время действия ссылки", reply_markup=nav.sub_inline_murk)

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
                    await update.set_payment_success(user_id, payment, payload)
                elif payment['status'] == 'canceled':
                    date_create_str = datetime.datetime.strptime(payment['created_at'][:19], "%Y-%m-%dT%H:%M:%S").strftime('%d-%m-%Y %H:%M')
                    await update.bot.send_message(user_id, f"Ваш платеж от {date_create_str} отменён, либо прошло время действия ссылки", reply_markup=nav.sub_inline_murk)

            await asyncio.sleep(7) #5 секунд ожидания каждого запроса, чтобы не заткнуть АПИ

    await asyncio.sleep(timedata) #ждем

async def reminder_send(timedata):
    list_reminders = db.get_users_reminder_days(config.DAYS_REMINDER)
    if list_reminders is not None:
        for reminder_row in list_reminders:
            user_id = reminder_row[0]
            await update.bot.send_message(user_id, texts.REMINDER)
            await db.set_last_active_time(user_id)

    await asyncio.sleep(timedata) #ждем

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def init():
    db.update_fields()

async def main():
    while True:
        await check_payment(10)
        await reminder_send(10)


if __name__ == '__main__':

    init()
    main()


    app = ApplicationBuilder().token(config.TOKEN).build()

    start_handler = CommandHandler('start', start)
    app.add_handler(start_handler)

    app.add_handler(CommandHandler("share", give_info))

    app.add_handler(CommandHandler("myprofile", profile_handler))

    app.add_handler(CommandHandler("subscribe", subscribe_handler))

    app.add_handler(CommandHandler("newtopic", new_topic))

    app.add_handler(CommandHandler("help", instruction_info))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send))

    app.add_handler(CallbackQueryHandler(handler_callback_query))

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    app.add_handler(unknown_handler)


    app.run_polling()