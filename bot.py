import telebot
from telebot.types import Message
from dotenv import load_dotenv
from os import getenv

load_dotenv()
token = getenv("BOT_TOKEN")

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start_command(message: Message):
    user_name = message.from_user.first_name
    bot.send_message(
        chat_id=message.chat.id,
        text=f"Приветствую тебя, {user_name}!"
    )


@bot.message_handler(commands=['help'])
def help_command(message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Я твой цифровой собеседник. Узнать обо мне подробнее можно командой /about"
    )


@bot.message_handler(commands=['about'])
def about_command(message: Message):
    text = "Рад, что ты заинтересован_а! Мое предназначение — не оставлять тебя в одиночестве и всячески подбадривать!"
    bot.send_message(
        chat_id=message.chat.id,
        text=text
    )


def filter_hello(message):
    word = "привет"
    return word in message.text.lower()


@bot.message_handler(content_types=['text'], func=filter_hello)
def say_hello(message: Message):
    user_name = message.from_user.first_name
    bot.send_message(
        chat_id=message.chat.id,
        text=f"{user_name}, приветики!"
    )


def filter_bye(message):
    word = "пока"
    return word in message.text.lower()


@bot.message_handler(content_types=["text"], func=filter_bye)
def say_bye(message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Пока, заходи ещё!"
    )

@bot.message_handler(commands=['GPT_assistant'])
def solve_task(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Следующим сообщением напиши промт"
    )
    bot.register_next_step_handler(
        message,
        get_promt
    )


def get_promt(message):
    if message.content_type != "text":
        bot.send_message(
            chat_id=message.chat.id,
            text="Отправь промт текстовым сообщением"
        )
        bot.register_next_step_handler(
            message,
            get_promt
        )
        return

    user_promt = message.text

    bot.send_message(
        chat_id=message.chat.id,
        text="Промт принят!"
    )


@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                               'text', 'location', 'contact', 'sticker'])
def send_echo(mesage: Message):
    text = (
        f"Вы отправили ({mesage.text}).\n"
        f"Но к сожалению я вас не понял😔, для общения со мной используйте встроенные кнопки.🤗"
    )
    bot.send_message(
        chat_id=mesage.chat.id,
        text=text
    )


bot.infinity_polling(none_stop=True)
