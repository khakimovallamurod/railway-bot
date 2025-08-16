from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_viloyats():
    stations = {
        "Toshkent": "2900000",
        "Samarqand": "2900700",
        "Buxoro": "2900800",
        "Xiva": "2903200",
        "Urganch": "2900790",#
        "Nukus": "2903000",
        "Navoiy": "2900900",
        "Andijon": "2902300",
        "Qarshi": "2901100",
        "Jizzax": "2900400",
        "Termiz": "2901500",
        "Guliston": "2900200",
        "Qo'qon": "2902000",
        "Margilon": "2900920",#
        "Pop": "2901900",
        "Namangan": "2902200",
    }
    keyboards_btns = []
    row = []
    for viloyat in stations:
        row.append(InlineKeyboardButton(text=viloyat, callback_data=f'{viloyat}:{stations[viloyat]}'))
        if len(row) == 2:
            keyboards_btns.append(row)
            row = []

    if row:
        keyboards_btns.append(row)

    return InlineKeyboardMarkup(
        keyboards_btns
    )
    
def poyezd_licanse(numbers):
    keyboards_btns = []
    row = []
    for num in numbers:
        row.append(KeyboardButton(text=num))
        if len(row) == 2:
            keyboards_btns.append(row)
            row = []
    if row:
        keyboards_btns.append(row)

    return ReplyKeyboardMarkup(
        keyboards_btns,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def signal_keyboard(train_number, date, route_key):
    """🚆 Har bir signal uchun alohida 'To‘xtatish' tugmasi (InlineKeyboardMarkup)"""
    keyboard = [
        [InlineKeyboardButton(f"⛔ {train_number} uchun to‘xtatish", callback_data=f"stop_signal:{route_key}:{train_number}:{date}")],
        [InlineKeyboardButton("✏️ Commentni o'zgartirish", callback_data=f"edit_comment:{route_key}:{train_number}:{date}")]
        ]
    return InlineKeyboardMarkup(keyboard)


def select_class_button():
    keyboard_btn = [
        [KeyboardButton(text="Econom"), KeyboardButton(text="Biznes"), KeyboardButton(text="VIP")],  
        [KeyboardButton(text="Kupe"), KeyboardButton(text="Platskart"), KeyboardButton(text="Sidячий")],  
        [KeyboardButton(text="ALL")]  
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard_btn, resize_keyboard=True)