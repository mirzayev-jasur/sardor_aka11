from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from keyboards import *
from database import *
from dotenv import load_dotenv
import os
from datetime import datetime
import asyncio
import logging
from aiogram.client.default import DefaultBotProperties
load_dotenv()

TOKEN = os.getenv('TOKEN')
PAYMENT = os.getenv('PAYMENT')

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()


@router.message(Command("start"))
async def command_start(message: Message):
    full_name = message.from_user.full_name
    await message.answer(f"Salom <b>{full_name}</b>\n"
                         f"7 Saber erkaklar onlayn do'koniga xush kelibsiz😊!")
    await register_user(message)


async def register_user(message: Message):
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    user = first_select_user(chat_id)
    if user:
        await message.answer(f"Salom {full_name}! Botimizga xush kelibsiz!Ⓜ️👚")
        await show_main_menu(message)
    else:
        first_register_user(chat_id, full_name)
        await message.answer("Ro'yxatdan o'tishingiz uchun kontaktingizni kiriting 📞",
                             reply_markup=phone_button())


@router.message(F.contact)
async def finish_register(message: Message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    update_user_to_finish_register_(chat_id, phone)
    await create_cart_for_user(message)
    await message.answer("Ro'yxatdan muvaffiqiyatli o'tdingiz 📰")
    await show_main_menu(message)


async def create_cart_for_user(message: Message):
    chat_id = message.chat.id
    try:
        insert_to_cart(chat_id)
    except:
        pass


async def show_main_menu(message: Message):
    await message.answer("Kategoriyani tanlang",
                         reply_markup=generate_main_menu())


@router.message(F.text.contains('✅ Buyurtma berish'))
async def make_order(message: Message):
    await message.answer("Bo'limni tanlang", reply_markup=generate_category_menu())


@router.callback_query(F.data.contains('category'))
async def show_products(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    _, category_id = callback.data.split('_')
    category_id = int(category_id)
    await callback.message.edit_text('<b>Kiyim tanlang</b>',
                                     reply_markup=shirts_by_category(category_id))
    await callback.answer()


@router.callback_query(F.data.contains('main-menu'))
async def return_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text("Bo'limni tanlang",
                                     reply_markup=generate_category_menu())
    await callback.answer()


@router.callback_query(F.data.contains('shirt'))
async def show_detail_shirt(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    _, shirt_id = callback.data.split('_')
    shirt_id = int(shirt_id)

    shirt = get_shirt_detail(shirt_id)
    await callback.message.delete()

    try:
        with open(shirt[-1], mode='rb') as image:
            await bot.send_photo(chat_id=chat_id, photo=image,
                                 caption=f"""{shirt[2]}

{shirt[4]}

{shirt[3]} so'm""", reply_markup=generate_shirt_detail_menu(shirt_id=shirt_id, category_id=shirt[1]))
    except:
        await bot.send_message(chat_id, f"""{shirt[2]}

{shirt[4]}

{shirt[3]} so'm""", reply_markup=generate_shirt_detail_menu(shirt_id=shirt_id, category_id=shirt[1]))

    await callback.answer()


@router.callback_query(F.data.contains('back'))
async def return_to_category(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    _, category_id = callback.data.split('_')
    await callback.message.delete()
    await bot.send_message(chat_id, 'Kiyimni tanlang', reply_markup=shirts_by_category(category_id))
    await callback.answer()


@router.callback_query(F.data.contains('cart'))
async def add_shirt_cart(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    _, shirt_id, quantity = callback.data.split('_')
    shirt_id, quantity = int(shirt_id), int(quantity)

    cart_id = get_user_cart_id(chat_id)
    shirt = get_shirt_detail(shirt_id)

    final_price = quantity * shirt[3]

    if insert_or_update_cart_shirt(cart_id, shirt[2], quantity, final_price):
        await callback.answer('Maxsulot qoshildi')
    else:
        await callback.answer('Soni ozgardi')


@router.message(F.text.contains('Sumka 🛍'))
async def show_cart(message: Message, edit_message: bool = False):
    chat_id = message.chat.id
    cart_id = get_user_cart_id(chat_id)

    try:
        update_total_shirt_total_price(cart_id)
    except Exception as e:
        print(e)
        await message.answer("Sumka bosh❌")
        return

    cart_shirts = get_cart_shirts(cart_id)
    total_shirts, total_price = get_total_shirts_price(cart_id)

    if total_shirts and total_price:
        text = 'Sizning sumka 🛍\n\n'
        i = 0
        for shirt_name, quantity, final_price in cart_shirts:
            i += 1
            text += f"""№{i}. {shirt_name}
Soni: {quantity}
Umumiy summasi: {final_price} so'm\n\n"""

        text += f"""Umumiy maxsulotlar soni: {total_shirts}
To'lashingiz kerak bo'lgan summa: {total_price} so'm"""

        await message.answer(text, reply_markup=generate_cart_menu(cart_id))
    else:
        await message.answer('Sumka bosh ❌')


@router.callback_query(F.data.contains('delete'))
async def delete_cart_shirt(callback: CallbackQuery):
    _, cart_shirt_id = callback.data.split('_')
    cart_shirt_id = int(cart_shirt_id)

    delete_cart_shirt_from_database(cart_shirt_id)
    await callback.answer("Maxsulot o'chirildi")

    # Update cart display
    chat_id = callback.message.chat.id
    cart_id = get_user_cart_id(chat_id)

    try:
        update_total_shirt_total_price(cart_id)
        cart_shirts = get_cart_shirts(cart_id)
        total_shirts, total_price = get_total_shirts_price(cart_id)

        if total_shirts and total_price:
            text = 'Sizning sumka 🛍\n\n'
            i = 0
            for shirt_name, quantity, final_price in cart_shirts:
                i += 1
                text += f"""№{i}. {shirt_name}
Soni: {quantity}
Umumiy summasi: {final_price} so'm\n\n"""

            text += f"""Umumiy maxsulotlar soni: {total_shirts}
To'lashingiz kerak bo'lgan summa: {total_price} so'm"""

            await callback.message.edit_text(text, reply_markup=generate_cart_menu(cart_id))
        else:
            await callback.message.delete()
            await bot.send_message(chat_id, 'Sumka bosh ❌')
    except:
        await callback.message.delete()
        await bot.send_message(chat_id, 'Sumka bosh ❌')


@router.callback_query(F.data.contains('order'))
async def create_order(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    _, cart_id = callback.data.split('_')
    cart_id = int(cart_id)
    time_order = datetime.now().strftime('%H:%M')
    date_order = datetime.now().strftime('%d.%m.%Y')

    cart_shirts = get_cart_shirts(cart_id)
    total_shirts, total_price = get_total_shirts_price(cart_id)

    if total_shirts and total_price:
        save_order_check(cart_id, total_shirts, total_price, time_order, date_order)
        order_check_id = get_order_check_id(cart_id)
        text = 'Sizning buyurtma 🛍\n\n'
        i = 0
        for shirt_name, quantity, final_price in cart_shirts:
            i += 1
            text += f"""№{i}. {shirt_name}
Soni: {quantity}
Umumiy summasi: {final_price} so'm\n\n"""
            save_order(order_check_id, shirt_name, quantity, final_price)

        text += f"""Umumiy maxsulotlar soni: {total_shirts}
To'lashingiz kerak bo'lgan summa: {total_price} so'm"""

        await bot.send_invoice(
            chat_id=chat_id,
            title=f'Buyurtma № {cart_id}',
            description=text,
            payload='bot-defined-invoice-payload',
            provider_token=PAYMENT,
            currency='UZS',
            prices=[
                LabeledPrice(label='Umumiy summa', amount=int(total_price * 100)),
                LabeledPrice(label='Yetkazib berish', amount=1500000)
            ],
            start_parameter='start_parameter'
        )
    await callback.answer()


@router.pre_checkout_query()
async def checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def get_payment(message: Message):
    chat_id = message.chat.id
    cart_id = get_user_cart_id(chat_id)
    await message.answer("Muvaffiqiyatli to'lov amalga oshirildi! 💸💸💸")
    drop_cart_shirts_default(cart_id)


@router.message(F.text.contains('Manzil 📍'))
async def send_location(message: Message):
    latitude = 41.331460522799354
    longitude = 69.28452392531489
    await bot.send_location(message.chat.id, latitude, longitude)
    await message.answer("Bizning manzil 📍")


@router.message(F.text.contains('Tarix 📜'))
async def show_history_orders(message: Message):
    chat_id = message.chat.id
    cart_id = get_user_cart_id(chat_id)
    order_check_info = get_order_check(cart_id)

    if not order_check_info:
        await message.answer("Sizda hali buyurtmalar tarixi yo'q")
        return

    for i in order_check_info:
        text = f"""Buyurtma sanasi: {i[-1]}
Buyurtma vaqti: {i[-2]}
Umumiy soni: {i[3]}
Umumiy summasi: {i[2]} so'm\n\n"""

        detail_order = get_detail_order(i[0])

        for j in detail_order:
            text += f"""Kiyim: {j[0]}
Soni: {j[1]}
Umumiy summasi: {j[2]} so'm\n\n"""

        await message.answer(text)


async def main():
    # Initialize database tables
    create_users_table()
    create_carts_table()
    create_cart_shirts_table()
    create_categories_table()
    create_shirts_table()
    orders_check()
    order()

    # Insert initial data
    try:
        insert_categories()
        insert_shirts_table()
    except:
        pass

    # Include router
    dp.include_router(router)

    # Start polling
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
