from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import *

def phone_button():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Kontakt jo'nating ☎️", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def generate_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='✅ Buyurtma berish')],
            [KeyboardButton(text='Tarix 📜'), KeyboardButton(text='Sumka 🛍'), KeyboardButton(text='Manzil 📍')]
        ],
        resize_keyboard=True
    )

def generate_category_menu():
    buttons = []
    buttons.append([InlineKeyboardButton(text='7 SABER', url='https://7saber.uz/')])
    
    categories = get_all_categoires()
    category_buttons = []
    for category in categories:
        btn = InlineKeyboardButton(text=category[1], callback_data=f'category_{category[0]}')
        category_buttons.append(btn)
    
    # Add category buttons in rows of 2
    for i in range(0, len(category_buttons), 2):
        row = category_buttons[i:i+2]
        buttons.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def shirts_by_category(category_id):
    shirts = get_shirts_by_category_id(category_id)
    buttons = []
    
    shirt_buttons = []
    for shirt in shirts:
        btn = InlineKeyboardButton(text=shirt[1], callback_data=f'shirt_{shirt[0]}')
        shirt_buttons.append(btn)
    
    # Add shirt buttons in rows of 2
    for i in range(0, len(shirt_buttons), 2):
        row = shirt_buttons[i:i+2]
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text='⬅️Ortga', callback_data='main-menu')])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def generate_shirt_detail_menu(shirt_id, category_id):
    buttons = []
    
    # Quantity buttons (1-9) in rows of 3
    quantity_buttons = []
    for i in range(1, 10):
        btn = InlineKeyboardButton(text=str(i), callback_data=f'cart_{shirt_id}_{i}')
        quantity_buttons.append(btn)
    
    for i in range(0, len(quantity_buttons), 3):
        row = quantity_buttons[i:i+3]
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text='⬅️Ortga', callback_data=f'back_{category_id}')])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def generate_cart_menu(cart_id):
    buttons = []
    buttons.append([InlineKeyboardButton(text='Buyurtmani tasdiqlash✅', callback_data=f'order_{cart_id}')])
    
    cart_shirts = get_cart_shirt_for_delete(cart_id)
    for cart_shirt_id, shirt_name in cart_shirts:
        buttons.append([InlineKeyboardButton(text=f"🗑 {shirt_name}", callback_data=f'delete_{cart_shirt_id}')])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
