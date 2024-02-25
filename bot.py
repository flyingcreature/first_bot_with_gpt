import telebot
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from dotenv import load_dotenv
from os import getenv
from gpt import GPT, logging

load_dotenv()
token = getenv("BOT_TOKEN")

bot = telebot.TeleBot(token)

gpt = GPT(system_content="Ты дружелюбный помощник по математике")


@bot.message_handler(commands=['start'])
def start_command(message: Message):
    user_name = message.from_user.first_name
    bot.send_message(
        chat_id=message.chat.id,
        text=f"Приветствую тебя, {user_name} 👋!"
    )


@bot.message_handler(commands=['help'])
def help_command(message: Message):
    text = (
        "👋 Я твой цифровой собеседник.\n\n"
        "Что бы воспользоваться функцией gpt помощника 🕵‍♀️ используй команду /gpt .\n\n"
        "Этот бот сделан на базе нейронной сети [mistralai/Mistral-7B-Instruct-v0.2], "
        "запущенной локально на компьютере разработчика.\n"
        "Поэтому не переживай если ты ожидаешь ответ на свой вопрос слишком долго ⏳.\n"
        "Нейросеть работает из-за всех сил💦."
    )
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
        text=f"{user_name}, приветики 👋!"
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


# Функция сборки клавиатуры
def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


@bot.message_handler(commands=['gpt'])
def solve_task(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Следующим сообщением напиши промт\n"
             "Можешь ввести любую задачу, и я постараюсь её решить\n\n"
             "-Если напишешь 'продолжи', я продолжу объяснять задачу\n\n"
             "-Для завершения диалога напиши 'Конец'",
        reply_markup=create_keyboard(["👉Продолжить👈", "Конец✋"])
    )
    bot.register_next_step_handler(
        message,
        get_promt,

    )


def get_promt(message):
    if message.content_type != "text":
        bot.send_message(
            chat_id=message.chat.id,
            text="Отправь промт текстовым сообщением",
            reply_markup=create_keyboard(["👉Продолжить👈", "Конец✋"])
        )
        bot.register_next_step_handler(
            message,
            get_promt
        )
        return

    user_promt = message.text

    # Проверка на максимальное число токенов в запросе
    request_tokens = gpt.count_tokens(user_promt)
    if request_tokens > gpt.MAX_TOKENS:
        bot.send_message(
            chat_id=message.chat.id,
            text="Запрос несоответствует кол-ву токенов. Исправьте запрос!",
            reply_markup=create_keyboard(["👉Продолжить👈", "Конец✋"])
        )
        # Возвращаем в начало функции, что бы пользователь написал свой запрос заново
        bot.register_next_step_handler(
            message,
            get_promt
        )

    if user_promt.lower() == "конец✋":
        gpt.clear_history()
        bot.send_message(
            chat_id=message.chat.id,
            text="Буду ждать тебя с новыми задачами",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Если всё прошло хорошо
    bot.send_message(
        chat_id=message.chat.id,
        text="Промт принят ✅!",
        reply_markup=create_keyboard(["👉Продолжить👈", "Конец✋"])
    )

    if user_promt.lower() != "👉Продолжить👈":
        gpt.clear_history()

    # Формирование промта
    json = gpt.make_promt(user_promt)

    # Отправка запроса
    resp = gpt.send_request(json)

    # Проверяем ответ на наличие ошибок и парсим его
    response = gpt.process_resp(resp)

    if not response[0]:
        logging.error(f"Не удалось выполнить запрос {response}")
        bot.send_message(
            chat_id=message.chat.id,
            text="Не удалось выполнить запрос...",
            reply_markup=create_keyboard(["👉Продолжить👈", "Конец✋"])
        )
    if user_promt.lower() == "👉Продолжить👈":
        gpt.save_history(response[1])
        bot.send_message(
            chat_id=message.chat.id,
            text=response[1],
            reply_markup=create_keyboard(["👉Продолжить👈", "Конец✋"])
        )
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text=response[1],
            reply_markup=create_keyboard(["👉Продолжить👈", "Конец✋"])
        )

        bot.register_next_step_handler(
            message,
            get_promt
        )


@bot.message_handler(commands=['debug'])
def send_logs(message):
    try:
        with open("log_file.txt", "rb") as f:
            bot.send_document(message.chat.id, f)
    except telebot.apihelper.ApiTelegramException:
        bot.send_message(
            chat_id=message.chat.id,
            text="Логов нет!"
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


logging.info("Бот запущен")
bot.infinity_polling(none_stop=True)
