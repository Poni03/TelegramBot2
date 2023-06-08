from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

'''
MAin menu
btDMD = KeyboardButton('Новая тема')
btProfile = KeyboardButton('👤 Профиль')
btBuy = KeyboardButton('💎Оформить подписку')
mainMenu = ReplyKeyboardMarkup(resize_keyboard = True)
mainMenu.add(btProfile, btBuy)
mainDMD = ReplyKeyboardMarkup(resize_keyboard = True)
mainDMD.add(btDMD, btProfile, btBuy)
'''
#InlineMenu
sub_inline_murk = InlineKeyboardMarkup(row_width=2)


btnSubMoth = InlineKeyboardButton(text="Месяц - 159 рублей", callback_data='submonth')
btnSubMoth3 = InlineKeyboardButton(text="3 Месяца - 477 рублей", callback_data='submonth3')
sub_inline_murk.add(btnSubMoth)