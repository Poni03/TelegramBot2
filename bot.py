import time 
import datetime
import logging
import config
import asyncio
import os
import deepai
import italygpt2

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.utils import executor
from aiogram.types import Message
from aiogram.utils.deep_linking import get_start_link, decode_payload
from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery

import markup as nav
from bot_db import Database
from bot_referral import Referr

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)
db = Database('db/db.db')

async def setup_bot_commands(dp):
    bot_commands = [
        types.BotCommand("/newtopic", "Новая тема"),
        types.BotCommand("/about", "информация о боте"),
        types.BotCommand("/instruction", "Инструкция"),
        types.BotCommand("/refferal", "Реферальная программа"),
        types.BotCommand("/myprofile", "Профиль"),
        types.BotCommand("/subscribe", "Оплата подписки"),
        ]
    await dp.bot.set_my_commands(bot_commands)


PRICE = types.LabeledPrice(label='Подписка на 1 месяц', amount=159*100)
REFFERAL_PRICE = types.LabeledPrice(label='Подписка на 1 месяц', amount=143*100)
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

            await message.answer(f"Привет! Я – GPT-Dialog, языковая модель ИИ на базе ChatGPT, которая здесь, чтобы помочь. Просто спроси, что тебя интересует.") #reply_markup=nav.mainMenu)

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
    await message.answer(f'''Работать со мной просто. Все, что вам нужно сделать, это ввести свои вопросы или подсказки, и я сгенерирую ответ на основе информации, на которой меня учили. Вот несколько советов для эффективного взаимодействия:
- Используйте кнопку /newtopic для того, чтобы начать новый разговор, не относящийся контекстом к предыдущему.
- Будьте ясны: формулируйте свои вопросы или подсказки четко и лаконично. Это помогает мне лучше понять ваши потребности и дать более точные ответы.
- Предоставьте контекст: при необходимости предоставьте соответствующий контекст или справочную информацию, чтобы помочь мне лучше понять тему или ситуацию, о которой вы говорите. Чем больше подробностей вы предоставите, тем более индивидуальными и полезными могут быть мои ответы.
- Задавайте уточняющие вопросы. Не стесняйтесь задавать уточняющие вопросы или запрашивать разъяснения, если это необходимо. Я здесь, чтобы помочь вам, поэтому не стесняйтесь вступать со мной в разговор.
- Будьте вежливее: не забывайте поддерживать уважительный и вежливый тон во время нашего взаимодействия. Хотя я - искусственный интеллект, я ценю доброе и вежливое общение.
- Есть ограничения в знаниях: хоть я и стараюсь предоставлять полезную и точную информацию, имейте в виду, что я не всегда могу иметь доступ к самой последней информации, и мои ответы не следует рассматривать как профессиональный совет.
Помните, я здесь, чтобы помочь вам и предоставить информацию в меру своих возможностей. Просто введите ваши запросы, и я сделаю все возможное, чтобы помочь вам!''')#, reply_markup=nav.mainDMD)
@dp.message_handler(commands=("about"))
async def give_info(message: types.Message) -> None:
    await message.answer(f'''Как искусственный интеллект, я стараюсь помогать людям разными способами. Я могу предоставлять информацию по широкому кругу тем, отвечать на вопросы, предлагать предложения и участвовать в беседах. Если кому-то нужна помощь в решении сложной проблемы, он ищет совета по определенному вопросу или просто желает дружеского разговора, я здесь, чтобы протянуть руку помощи.
Я стремлюсь предоставлять точную и полезную информацию, способствуя обучению и обмену знаниями. Однако важно отметить, что, хотя я могу генерировать ответы на основе шаблонов данных, на которых меня обучали, я не обладаю личным опытом, эмоциями или сознанием. Моя цель — давать полезные и информативные ответы на основе данных, на которых меня учили, но меня всегда следует использовать как инструмент для расширения человеческих возможностей, а не как замену профессионального совета или критического мышления.
Таким образом, я являюсь языковой моделью ИИ, созданной для того, чтобы помогать и предоставлять информацию в меру своих возможностей. Моя цель — помогать людям, генерируя актуальные и ценные ответы, облегчая беседы и поддерживая пользователей в их начинаниях.''')#, reply_markup=nav.mainDMD)
@dp.message_handler(commands=("refferal"))
async def give_info(message: types.Message) -> None:
    await message.answer(f'''Реферальная программа: заработайте дополнительные дни бесплатного использования бота Telegram на основе подписки
Мы рады представить нашу реферальную программу, предназначенную для вознаграждения наших уважаемых пользователей за распространение информации о нашем боте на основе подписки. Благодаря нашей реферальной программе у вас есть возможность продлить бесплатное использование бота, пригласив своих друзей, а также дав им дополнительный стимул присоединиться.
Вот как работает реферальная программа:
Период тестирования: когда вы впервые начнете использовать нашего бота, у вас будет один день, чтобы бесплатно изучить его возможности и функции. Это позволит вам ознакомиться с тем, что может предложить наш бот, прежде чем принять решение о подписке.
Приглашение рефералов: после того, как вы попробуете бота и, если будете удовлетворены его возможностями, вы можете пригласить своих друзей и знакомых присоединиться. Поделитесь своей уникальной реферальной ссылкой в графе /Myprofile
Бесплатное использование для вас: если ваш приглашенный друг решит подписаться и заплатит за месяц подписки бота, вы получите автоматическое продление на 5 дней бесплатного использования в дополнение к вашей существующей подписке. Это наш способ отблагодарить вас за рекомендацию нашего бота другим.
Выгода для приглашенных рефералов: не только вы получаете выгоду от успешных рефералов, но и ваши приглашенные друзья! Они получат скидку на первый месяц использования в размере 10%!
Наслаждайтесь постоянными преимуществами: по мере того, как вы набираете успешных рефералов, вы можете наслаждаться расширенным периодом бесплатного использования бота.
Мы считаем, что наша реферальная программа обеспечивает беспроигрышную ситуацию как для вас, так и для ваших приглашенных друзей. Это позволяет вам продлить бесплатное использование бота, в то время как ваши друзья получают скидку при оплате.
Спасибо за то, что являетесь частью нашего сообщества и помогаете нам расти. Мы ценим вашу поддержку и надеемся, что наш бот будет полезен и ценен в вашей повседневной деятельности. Если у вас есть дополнительные вопросы или вам нужна помощь, не стесняйтесь обращаться в нашу службу поддержки: ______________ (сюда пропишем юзера в Телеграм, надо создать аккаунт отдельный)''')#,reply_markup=nav.mainDMD )

@dp.message_handler(commands="newtopic")
@dp.message_handler(lambda message: message.text and 'новая тема' in message.text.lower())
async def new_topic(message: types.Message) -> None:
    try:
        user_id = message.from_user.id
        messages[user_id] = []
        messages[user_id].append({"role": "user", "content": "изначально ответы на русском языке"})

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
    await message.answer(f'Дата окончания вашей подписки: {user_sub}\nВаша реферальная ссылка, чтобы поделиться с друзьями:\nhttps://telegram.me/{name}?start={encrypted_link}\nКоличество ваших рефералов: {db.count_referral(message.from_user.id)}')

@dp.message_handler(commands="subscribe")
@dp.message_handler(lambda message: message.text and 'submonth' in message.text.lower()) 
async def subscribe_handler(message: types.Message):
    try:
        if config.PAYMENTS_TOKEN.split(':')[1] == 'TEST':
            await message.answer("С нашей интегрированной платежной системой, встроенной непосредственно в Telegram, вы можете быть уверены, что все транзакции проводятся в соответствии с законодательством. Оплатить подписку вы можете с помощью банковской карты. После оплаты вы получаете электронный чек. И ссылка на оплату")
            if db.get_user_id(message.from_user.id):
                await bot.send_invoice(message.chat.id,
                    title="Подписка на бота",
                    description="Активация подписки на бота на 30 дней, скидка за реферальную систему 10%",
                    provider_token=config.PAYMENTS_TOKEN,
                    currency="rub",
                    photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
                    photo_width=416,
                    photo_height=234,
                    photo_size=416,
                    is_flexible=False,
                    prices=[REFFERAL_PRICE],
                    start_parameter="one-month-subscription",
                    payload="moth_sub")
            else:
                await bot.send_invoice(message.chat.id,
                    title="Подписка на бота",
                    description="Активация подписки на бота на 30 дней",
                    provider_token=config.PAYMENTS_TOKEN,
                    currency="rub",
                    photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
                    photo_width=416,
                    photo_height=234,
                    photo_size=416,
                    is_flexible=False,
                    prices=[PRICE],
                    start_parameter="one-month-subscription",
                    payload="moth_sub")
    except Exception as e:
        logging.error(f'Error in subscribe: {e}')

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
                messages[user_id].append({"role": "user", "content": "изначально ответы на русском языке"})

            messages[user_id].append({"role": "user", "content": user_message})
            # messages[user_id].append({"role": "user", "content": f"chat: {message.chat} Сейчас {time.strftime('%d/%m/%Y %H:%M:%S')} user: {message.from_user.first_name} message: {message.text}"})
            # Generate a response using OpenAI's Chat API
            #account_data = italygpt2.Account.create()
            #chatgpt_response_text = "".join(italygpt2.Completion.create(account_data=account_data,prompt="на русском языке",message=messages[user_id]))
            chatgpt_response_text = "".join(deepai.ChatCompletion.create(messages=messages[user_id]))
            # Add the bot's response to the user's message history
            messages[user_id].append({"role": "assistant", "content": chatgpt_response_text})

            await message.answer(chatgpt_response_text) #reply_markup=nav.mainDMD)

            await db.increment_counter_msg(user_id)
            await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)

        else:
            await message.answer(f"Закончилось время подписки. Пожалуйста, оформите подписку!", reply_markup=nav.sub_inline_murk)

    except Exception as ex:
        # If an error occurs, try starting a new topic
        await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
        print(ex)
        if ex == "context_length_exceeded":
            await message.reply('У бота закончилась память, пересоздаю диалог',rparse_mode='Markdown')
            await new_topic(message)
            await send(message)
        else:
            await message.reply('У бота возникла ошибка, подождите некоторое время и попробуйте снова', parse_mode='Markdown')

# pre checkout  (must be answered in 10 seconds)
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


# successful payment
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    try:
        if message.successful_payment.invoice_payload == "moth_sub":
            db.add_date_sub(message.from_user.id, config.DAYS_ADD_TO_PAYMENT)
            await message.answer(f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!\n Подзравляю вам выдана подписка на 30 дней!")

            referral_id = db.get_referral_id(message.from_user.id)
            print(referral_id)
            if referral_id is not None:
                if (not db.get_date_status(message.from_user.id)):
                    db.add_date_sub(referral_id, config.DAYS_ADD_FOR_REFFERAL)
                    await bot.send_message(referral_id, f'Ваша подписка продлена на {config.DAYS_ADD_FOR_REFFERAL} дней, по Вашей реферальной ссылке зачислены средства')#reply_markup=nav.mainMenu)

    except Exception as e:
        logging.error(f'Error in payment: {e}')

if __name__ == '__main__':
	executor.start_polling(dp, skip_updates = True, on_startup=setup_bot_commands)