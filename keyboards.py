from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_viloyats():
    stations = {
        "Toshkent": "2900000",
        "Samarqand": "2900700",
        "Buxoro": "2900800",
        "Navoiy": "2900900",
        "Qarshi": "2901100",
        "Termiz": "2901500",
        "Farg‘ona": "2902100",
        "Andijon": "2902300",
        "Namangan": "2902200",
        "Qo‘qon": "2902000",
        "Pop": "2901900",
        "Nukus": "2903000",
        "Urganch": "2903100",
        "Xiva": "2903200",
        "Jizzax": "2900400",
        "Guliston": "2900200"
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

def signal_keyboard(train_number, date):
    """🚆 Har bir signal uchun alohida 'To‘xtatish' tugmasi (InlineKeyboardMarkup)"""
    keyboard = [[InlineKeyboardButton(f"⛔ {train_number} uchun to‘xtatish", callback_data=f"stop_signal:{train_number}:{date}")]]
    return InlineKeyboardMarkup(keyboard)


def select_class_button():
    keyboard_btn = [
        [KeyboardButton(text="Econom"), KeyboardButton(text="Biznes"), KeyboardButton(text="VIP")],  
        [KeyboardButton(text="Kupe"), KeyboardButton(text="Platskart"), KeyboardButton(text="Sidячий")],  
        [KeyboardButton(text="ALL")]  
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard_btn, resize_keyboard=True)