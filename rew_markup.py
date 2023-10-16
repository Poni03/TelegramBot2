from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update


# Enable logging

keyboard = [

    [

        InlineKeyboardButton("Месяц - 199 рублей", callback_data="submonth_1"),

        InlineKeyboardButton("3 Месяца - 477 рублей", callback_data="submonth_3"),

    ]

]

keyboard_button = [

    [

        KeyboardButton("Новая тема"),

        KeyboardButton("👤 Профиль"),

    ]

]

inline_payments_choice = InlineKeyboardMarkup(keyboard)
keyboard_button = ReplyKeyboardMarkup(keyboard_button, resize_keyboard=True)