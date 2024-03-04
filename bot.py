import telebot
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from dotenv import load_dotenv
from os import getenv
from config import LOGS_PATH, MAX_TASK_TOKENS, USER_DATA_PATH
from gpt import ask_gpt_helper, count_tokens, logging
from utils import create_keyboard, load_data, save_data

load_dotenv()
token = getenv("BOT_TOKEN")

bot = telebot.TeleBot(token)


user_data = load_data(USER_DATA_PATH)


# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.username
    user_id = message.chat.id

    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "user_name": user_name,
            "current_task": None,
            "current_answer": None,
        }
        save_data(user_data, USER_DATA_PATH)

    bot.send_message(
        user_id,
        f"Привет, {user_name} 👋! Я бот-помощник для решения задач по разным предметам!\n"
        f"Ты можешь прислать свой вопрос, а я постараюсь на него ответить.\n"
        "Иногда ответы получаются слишком длинными - в этом случае ты можешь попросить продолжить.",
        reply_markup=create_keyboard(["Задать новый вопрос"]),
    )
    bot.register_next_step_handler(message, solve_task)


# Необходимый для обработки фильтр
def filter_solve_task(message: Message) -> bool:
    return message.text == "Задать новый вопрос"


# Обработчик запроса "Задать новый вопрос"
@bot.message_handler(func=filter_solve_task)
def solve_task(message):
    bot.send_message(message.chat.id, "Напиши условие задачи:")
    bot.register_next_step_handler(message, give_answer)


def give_answer(message: Message):
    user_id = message.chat.id

    if count_tokens(message.text) <= MAX_TASK_TOKENS:  # Если уложились в лимит токенов
        bot.send_message(message.chat.id, "Решаю...")
        answer = ask_gpt_helper(message.text)  # Получаем ответ от gpt

        user_data[str(user_id)][
            "current_task"
        ] = message.text  # Запоминаем текущую задачу
        user_data[str(user_id)]["current_answer"] = answer  # Запоминаем ответ gpt
        save_data(user_data, USER_DATA_PATH)

        if answer is None:  # Если ошибка в gpt
            bot.send_message(
                user_id,
                "Не могу получить ответ от GPT :(",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )
        elif answer == "":  # Если ошибки нет, но ответ пустой
            bot.send_message(
                user_id,
                "Не могу сформулировать решение :(",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )
            logging.info(
                f"Отправлено: {message.text}\nПолучена ошибка: нейросеть вернула пустую строку"
            )
        else:  # Если всё ок
            bot.send_message(
                user_id,
                answer,
                reply_markup=create_keyboard(
                    ["Задать новый вопрос", "Продолжить объяснение"]
                ),
            )

    else:  # Если задача слишком большая
        user_data[str(user_id)]["current_task"] = None
        user_data[str(user_id)]["current_answer"] = None
        save_data(user_data, USER_DATA_PATH)

        bot.send_message(
            message.chat.id,
            "Текст задачи слишком длинный. Пожалуйста, попробуй его укоротить.",
        )
        logging.info(
            f"Отправлено: {message.text}\nПолучено: Текст задачи слишком длинный"
        )


def filter_continue_explaining(message: Message) -> bool:
    return message.text == "Продолжить объяснение"


# Обработчик запроса "Продолжить объяснение"
@bot.message_handler(func=filter_continue_explaining)
def continue_explaining(message: Message):
    user_id = message.chat.id

    if not user_data[str(user_id)][
        "current_task"
    ]:  # Если просят продолжить, но ещё не ввели задачу
        bot.send_message(
            user_id,
            "Для начала напиши условие задачи:",
            reply_markup=create_keyboard(["Задать новый вопрос"]),
        )

    else:
        bot.send_message(user_id, "Формулирую продолжение...")
        answer = ask_gpt_helper(
            user_data[str(user_id)]["current_task"],
            user_data[str(user_id)]["current_answer"],
        )
        user_data[str(user_id)][
            "current_answer"
        ] += answer  # Добавляем новый кусочек объяснения к сохранённому ответу
        save_data(user_data, USER_DATA_PATH)

        if answer is None:  # Если ошибка gpt
            bot.send_message(
                user_id,
                "Не могу получить ответ от GPT :(",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )
        elif answer == "":  # Если пустой ответ, продолжать некуда
            bot.send_message(
                user_id,
                "Задача полностью решена ^-^",
                reply_markup=create_keyboard(["Задать новый вопрос"]),
            )
        else:
            bot.send_message(
                user_id,
                answer,
                reply_markup=create_keyboard(
                    ["Задать новый вопрос", "Продолжить объяснение"]
                ),
            )


@bot.message_handler(commands=['help'])
def help_command(message: Message):
    text = (
        "👋 Я твой цифровой собеседник.\n\n"
        "Что бы воспользоваться функцией gpt помощника 🕵‍♀️ следуй инструкциям бота .\n\n"
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


@bot.message_handler(commands=['debug'])
def send_logs(message):
    try:
        with open(LOGS_PATH, "rb") as f:
            bot.send_document(
                message.chat.id,
                f
            )
    except telebot.apihelper.ApiTelegramException:
        bot.send_message(
            chat_id=message.chat.id,
            text="Логов нет!"
        )


@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                               'text', 'location', 'contact', 'sticker'])
def send_echo(message: Message):
    text = (
        f"Вы отправили ({message.text}).\n"
        f"Но к сожалению я вас не понял😔, для общения со мной используйте встроенные кнопки.🤗"
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text
    )


logging.info("Бот запущен")
bot.infinity_polling(none_stop=True)











