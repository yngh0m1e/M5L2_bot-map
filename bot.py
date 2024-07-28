import telebot
from config import *
from logic import *
import colorsys
import random

bot = telebot.TeleBot(TOKEN)

# Словарь для хранения выбранных цветов маркеров пользователей
user_colors = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который может показывать города на карте. Напиши /help для списка команд.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, "Доступные команды:")
    bot.send_message(message.chat.id, "/show_city [город] - Показать город на карте.\n"
                                      "/remember_city [город] - Запомнить город.\n"
                                      "/show_my_cities - Показать все сохраненные города.\n"
                                      "/set_marker_color - Установить цвет маркера.")

@bot.message_handler(commands=['set_marker_color'])
def handle_set_marker_color(message):
    # Предложим пользователю выбрать цвет из доступных
    color_options = "Доступные цвета: красный, зеленый, синий, желтый, фиолетовый, черный."
    bot.send_message(message.chat.id, color_options)
    bot.send_message(message.chat.id, "Введите команду в формате: /color [цвет]. Например, /color красный")

@bot.message_handler(commands=['color'])
def handle_color_choice(message):
    user_id = message.chat.id
    color_name = message.text.split()[-1].lower()

    # Словарь для сопоставления названий цветов с кодами цветов
    color_map = {
        'красный': 'red',
        'зеленый': 'green',
        'синий': 'blue',
        'желтый': 'yellow',
        'фиолетовый': 'purple',
        'черный': 'black'
    }

    if color_name in color_map:
        # Сохраняем выбранный цвет для пользователя
        user_colors[user_id] = color_map[color_name]
        bot.send_message(user_id, f"Цвет маркера установлен на {color_name}.")
    else:
        bot.send_message(user_id, "Неверный цвет. Попробуйте снова.")

@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    city_name = message.text.split()[-1]
    user_id = message.chat.id

    # Получаем цвет, выбранный пользователем, или используем цвет по умолчанию
    color = user_colors.get(user_id, 'blue')

    manager.create_graph(f'{user_id}.png', [city_name], color=color)
    with open(f'{user_id}.png', 'rb') as map:
        bot.send_photo(user_id, map)

@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    user_id = message.chat.id
    city_name = message.text.split()[-1]
    city = manager.get_city(city_name)
    if city:
        manager.create_graph(f'{user_id}.png', [city])
    else:
        bot.send_message(message.chat.id, 'Такого города я не знаю. Убедитесь, что он написан на английском!')

@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    cities = manager.select_cities(message.chat.id)
    if cities:
        manager.create_graph(f'{message.chat.id}_cities.png', cities)
        with open(f'{message.chat.id}_cities.png', 'rb') as map:
            bot.send_photo(message.chat.id, map)
    else:
        bot.send_message(message.chat.id, "У вас пока нет сохранённых городов.")

if __name__=="__main__":
    manager = DB_Map(DATABASE)
    bot.polling()
