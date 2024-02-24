import telebot
from telebot.types import Message
from dotenv import load_dotenv
from os import getenv
from gpt import GPT

load_dotenv()
token = getenv("BOT_TOKEN")

bot = telebot.TeleBot(token)

gpt = GPT(system_content="Ты дружелюбный помощник по математике")


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
        text="Я твой цифровой собеседник."
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


@bot.message_handler(commands=['gpt'])
def solve_task(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Следующим сообщением напиши промт\n"
             "Можешь ввести любую задачу, и я постараюсь её решить\n\n"
             "-Если напишешь 'продолжи', я продолжу объяснять задачу\n\n"
             "-Для завершения диалога напиши 'конец'"
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

    if user_promt.lower() == "конец":
        gpt.clear_history()
        return

    request_tokens = gpt.count_tokens(user_promt)
    if request_tokens > gpt.MAX_TOKENS:
        bot.send_message(
            chat_id=message.chat.id,
            text="Запрос несоответствует кол-ву токенов. Исправьте запрос!"
        )
        bot.register_next_step_handler(
            message,
            get_promt
        )

    if user_promt.lower() == "продолжи":
        gpt.clear_history()

    json = gpt.make_promt(user_promt)

    resp = gpt.send_request(json)

    response = gpt.send_request(resp)
    if not response[0]:
        bot.send_message(
            chat_id=message.chat.id,
            text="Не удалось выполнить запрос..."
        )
    bot.send_message(
        chat_id=message.chat.id,
        text=response[1]
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
