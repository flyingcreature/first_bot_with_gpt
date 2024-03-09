import telebot
from telebot.types import Message, ReplyKeyboardRemove
from dotenv import load_dotenv
from os import getenv
from config import LOGS_PATH, MAX_TASK_TOKENS
from gpt import ask_gpt_helper, count_tokens, logging
from utils import create_keyboard

load_dotenv()
token = getenv("BOT_TOKEN")

bot = telebot.TeleBot(token)

user_data = {}
# Инициализируем словарь соответствия: "команда": "то, что пойдет в промты gpt"

command_to_subject = {
    "math": "математике",
    "rus": "русскому языку"
}

command_to_level = {
    "beginner": "начинающего",
    "advanced": "продвинутого"
}


@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.username
    user_id = message.chat.id

    if user_id not in user_data:
        user_data[user_id] = {
            "user_name": user_name,
            "current_subjects": "",
            "current_levels": "",
            "current_tasks": "",
            "current_answers": ""
        }
        print(user_data)

    bot.send_message(
        user_id,
        f"Привет, {user_name} 👋! Я бот-помощник для решения задач по разным предметам!\n"
        f"Ты можешь прислать свой вопрос, а я постараюсь на него ответить.\n"
        "Иногда ответы получаются слишком длинными - в этом случае ты можешь попросить продолжить.",
        reply_markup=create_keyboard(["Задать новый вопрос"]),
    )


def filter_send_keyboard_subject(message: Message) -> bool:
    return message.text.lower() in ["задать новый вопрос", "изменить предмет/сложность"]


@bot.message_handler(func=filter_send_keyboard_subject)
def send_keyboard_subject(message):
    user_id = message.chat.id
    if user_data[user_id]["current_subjects"] == "" or message.text.lower() == "изменить предмет/сложность":
        bot.send_message(
            user_id,
            "Выбери предмет",
            reply_markup=create_keyboard(["math", "rus"])
        )
        bot.register_next_step_handler(message, choose_subject)

    else:
        bot.send_message(
            user_id,
            "Напиши условие задачи:",
        )
        bot.register_next_step_handler(message, give_answer)


def filter_choose_subject(message):
    return message.text.lower() in ["math", "rus"]


# Обработка нужного предмета
@bot.message_handler(func=filter_choose_subject)
def choose_subject(message: Message):
    user_id = message.chat.id
    if message.text.lower() not in ["math", "rus"]:
        bot.send_message(
            user_id,
            "Выбери предмет из предложенных вариантов ('math' или 'rus')",
        )
        bot.register_next_step_handler(message, choose_subject)  # Запрашиваем у пользователя выбор предмета повторно
    else:
        text = (
            "Выбери уровень сложности ответа:\n"     
            "beginner - начинающий\n"
            "advanced - продвинутый"
            )

        subject = command_to_subject.get(message.text.lower())  # Получаем из словаря название предмета
        user_data[user_id]["current_subjects"] = subject  # Запоминаем выбранный предмет
        print(subject)
        print(user_data)
        bot.send_message(
            user_id,
            text=text,
            reply_markup=create_keyboard(["Beginner", "Advanced"])
        )
        bot.register_next_step_handler(message, choose_level)


def filter_choose_level(message):
    return message.text.lower() in ["beginner", "аdvanced"]


# Обработка нужного уровня
@bot.message_handler(func=filter_choose_level)
def choose_level(message: Message):
    user_id = message.chat.id
    if message.text.lower() not in ["beginner", "advanced"]:
        bot.send_message(
            user_id,
            text="Выбери уровень сложности ответа из предложенных вариантов ('Beginner' или 'Advanced')"
        )
        bot.register_next_step_handler(message, choose_level)
    else:
        levels = command_to_level.get(message.text.lower())  # Получаем из словаря уровень сложности
        user_data[user_id]["current_levels"] = levels  # Запоминаем выбранный уровень
        print(levels)
        print(user_data)
        bot.send_message(
            user_id,
            "Напиши условие задачи:",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(message, give_answer)


def give_answer(message: Message):
    user_id = message.chat.id
    # Достаём из словаря предмет и lvl, что бы включить его в блок с gpt
    subject = user_data[user_id]["current_subjects"]
    levels = user_data[user_id]["current_levels"]

    if count_tokens(message.text) <= MAX_TASK_TOKENS:  # Если уложились в лимит токенов
        bot.send_message(message.chat.id, "Решаю...")
        answer = ask_gpt_helper(message.text, subject, levels)  # Получаем ответ от gpt
        user_data[user_id]["current_tasks"] = message.text  # Запоминаем текущую задачу
        user_data[user_id]["current_answers"] = answer  # Запоминаем ответ gpt

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
                    ["Задать новый вопрос", "Продолжить объяснение", "Изменить предмет/сложность"]
                ),
            )

    else:  # Если задача слишком большая
        user_data[user_id]["current_tasks"] = ""  # Обнуляем текущую задачу
        user_data[user_id]["current_answers"] = ""  # Обнуляем ответ gpt

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

    if user_data[user_id]["current_tasks"] == "":  # Если просят продолжить, но ещё не ввели задачу
        bot.send_message(
            user_id,
            "Для начала напиши условие задачи:",
            reply_markup=create_keyboard(["Задать новый вопрос"]),
        )

    else:
        bot.send_message(user_id, "Формулирую продолжение...")
        answer = ask_gpt_helper(
            user_data[user_id]["current_tasks"],
            user_data[user_id]["current_subjects"],
            user_data[user_id]["current_levels"],
            user_data[user_id]["current_answers"]
        )
        user_data[user_id]["current_answers"] += answer  # Добавляем новый кусочек объяснения к сохранённому ответу

        if answer is None:  # Если ошибка gpt
            bot.send_message(
                user_id,
                "Не могу получить ответ от GPT :(",
                reply_markup=create_keyboard(["Задать новый вопрос", "Изменить предмет/сложность"]),
            )
        elif answer == "":  # Если пустой ответ, продолжать некуда
            bot.send_message(
                user_id,
                "Задача полностью решена ^-^",
                reply_markup=create_keyboard(["Задать новый вопрос", "Изменить предмет/сложность"]),
            )
        else:
            bot.send_message(
                user_id,
                answer,
                reply_markup=create_keyboard(
                    ["Задать новый вопрос", "Продолжить объяснение", "Изменить предмет/сложность"]
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
        text=text,
        reply_markup=ReplyKeyboardRemove()
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
