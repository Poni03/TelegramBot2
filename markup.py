from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

#MAin menu
btDMD = KeyboardButton('Новая тема')
btProfile = KeyboardButton('👤 Профиль')
btBuy = KeyboardButton('Помощь')
mainMenu = ReplyKeyboardMarkup(resize_keyboard = True)
mainMenu.add(btProfile, btBuy)
mainDMD = ReplyKeyboardMarkup(resize_keyboard = True)
mainDMD.add(btDMD, btProfile)

#share_markup = telegram.ReplyKeyboardMarkup([[telegram.KeyboardButton("Поделиться", request_contact=True)]], resize_keyboard=True)

#InlineMenu
sub_inline_murk = InlineKeyboardMarkup(row_width=2)


btnSubMoth = InlineKeyboardButton(text="Месяц - 199 рублей", callback_data='submonth_1')
btnSubMoth3 = InlineKeyboardButton(text="3 Месяца - 477 рублей", callback_data='submonth_3')
sub_inline_murk.add(btnSubMoth)
sub_inline_murk.add(btnSubMoth3)