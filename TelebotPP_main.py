import sys
import mysql
import telebot
from Tools.scripts.mkreal import join
from mysql.connector import errorcode
from telebot import types, TeleBot
import const
from geopy.distance import geodesic

# Подключение к БД
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        port="3306",
        database="telebotPP"
    )


# проверка на ошибки
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Ошибка! Проверьте имя и пароль!")
        sys.exit()
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Такая база данных не существует!")
        sys.exit()
    else:
        print(err)
        sys.exit()

cursor = db.cursor()


# Токен бота
bot: TeleBot = telebot.TeleBot(const.API_TOKEN, parse_mode=None)

# Меню
markup_menu = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                        row_width=2)  # Клавиатура меню. подгон под размер, в одной строке

markup_shop = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

markup_our_shops = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

# Кнопки
btn_catalog = types.KeyboardButton('Каталог 📖')
btn_shop = types.KeyboardButton('Наши магазины 🏪')
# btn_website = types.KeyboardButton('Наш сайт 🌐')
btn_nearest_shop = types.KeyboardButton('Показать ближайший к Вам магазин 🔽', request_location=True)
btn_back_to_menu = types.KeyboardButton('Вернуться в меню ⬅')
btn_shop1 = types.KeyboardButton('Магазин в Николино 🏡')
btn_shop2 = types.KeyboardButton('Питомник в Рябинках 🌿')

# Добавление кнопок в меню
markup_menu.add(btn_catalog, btn_shop, btn_nearest_shop)

markup_our_shops.add(btn_shop1, btn_shop2, btn_back_to_menu)

markup_inline_shop = types.InlineKeyboardMarkup(row_width=1)

# btn_in_shop_1 = types.InlineKeyboardButton('Магазин в Николино 🏡', callback_data='shop_1')
# btn_in_shop_2 = types.InlineKeyboardButton('Питомник в Рябинках 🌿', callback_data='shop_2')

# markup_inline_shop.add(btn_in_shop_1, btn_in_shop_2)

markup_inline_catalog = types.InlineKeyboardMarkup(row_width=1)

btn_deciduous = types.InlineKeyboardButton('Лиственные 🌿', callback_data='deciduous')
btn_perennials = types.InlineKeyboardButton('Многолетники 🌳', callback_data='perennials')
btn_fruit = types.InlineKeyboardButton('Плодовые 🍏', callback_data='fruit')
btn_conifers = types.InlineKeyboardButton('Хвойные 🌲', callback_data='conifers')
btn_search = types.InlineKeyboardButton('Поиск по названию 🔎', callback_data='search')

markup_inline_catalog.add(btn_deciduous, btn_perennials, btn_fruit, btn_conifers, btn_search)


# обработчик событий, свойство commands команды start, help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Здравствуйте, " + message.from_user.first_name + ". Я бот Planet Plant's!",
                     reply_markup=markup_menu)


@bot.message_handler(func=lambda message: True)
def echo(message):
    if message.text == 'Наши магазины 🏪':
        bot.send_message(message.chat.id, 'В данный момент открыты следующие магазины', reply_markup=markup_our_shops)

    elif message.text == 'Наш сайт 🌐':
        bot.send_message(message.chat.id, const.WEB_URL)

    elif message.text == 'Каталог 📖':
        bot.send_message(message.chat.id, 'Выберите категорию товаров', reply_markup=markup_inline_catalog)

    elif message.text == 'Вернуться в меню ⬅':
        bot.send_message(message.chat.id, 'Вы вернулись в меню', reply_markup=markup_menu)

    elif message.text == 'Магазин в Николино 🏡':
        bot.send_venue(message.chat.id, const.SHOP_1['latm'], const.SHOP_1['lonm'],
                       const.SHOP_1['title'], const.SHOP_1['address'], reply_markup=markup_our_shops)

    elif message.text == 'Питомник в Рябинках 🌿':
        bot.send_venue(message.chat.id, const.SHOP_2['latm'], const.SHOP_2['lonm'],
                       const.SHOP_2['title'], const.SHOP_2['address'], reply_markup=markup_our_shops)

    else:
        bot.reply_to(message, message.text, reply_markup=markup_menu)


# Вывод геометок магазинов
@bot.callback_query_handler(func=lambda call: True)
def call_back_shops(call):
    print(call)
    product = ''

    # if call.data == 'shop_1':
    #
    #     bot.send_venue(call.message.chat.id, const.SHOP_1['latm'], const.SHOP_1['lonm'],
    #                    const.SHOP_1['title'], const.SHOP_1['address'])
    # elif call.data == 'shop_2':
    #     bot.send_venue(call.message.chat.id, const.SHOP_2['latm'], const.SHOP_2['lonm'],
    #                    const.SHOP_2['title'], const.SHOP_2['address'])

    if call.data == 'deciduous':
        sql = "SELECT NAME, DESCRIPTION, COST, PHOTO FROM product WHERE ID_CATEGORY_FK = %s"
        val = ("3", )
        cursor.execute(sql, val)
        product = cursor.fetchall()

    for x in product:
        print(x)
        bot.send_message(call.message.chat.id, '\n'.join(str(a) for a in x))

    else:
        bot.reply_to(call.message, call.message.text, reply_markup=markup_shop)


# Вычисление ближайшего к пользователю магазина
@bot.message_handler(func=lambda message: True, content_types=['location'])
def shops_location(message):
    print(message)
    lon = message.location.longitude  # Широта
    lat = message.location.latitude  # Долгота

    distance = []
    for m in const.SHOPS:
        result = geodesic((m['latm'], m['lonm']), (lat, lon))
        distance.append(result)
    index = distance.index(min(distance))

    bot.send_message(message.chat.id, 'Ближайший к вам магазин')
    bot.send_venue(message.chat.id, const.SHOPS[index]['latm'], const.SHOPS[index]['lonm'],
                   const.SHOPS[index]['title'], const.SHOPS[index]['address'])
    print('долгота {} широта {}'.format(lat, lon))  # вывод координат пользователя









bot.polling()
