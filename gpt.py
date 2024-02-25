import requests
import logging
from transformers import AutoTokenizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)


class GPT:
    def __init__(self, system_content=""):
        self.system_content = system_content
        self.URL = 'http://localhost:1234/v1/chat/completions'
        self.HEADERS = {"Content-Type": "application/json"}
        self.MAX_TOKENS = 150
        self.assistant_content = "Решим задачу по шагам: "

    # Подсчитываем количество токенов в промте
    @staticmethod
    def count_tokens(prompt):
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")  # название модели
        return len(tokenizer.encode(prompt))

    # Проверка ответа на возможные ошибки и его обработка
    def process_resp(self, response) -> [bool, str]:
        # Проверка статус кода
        if response.status_code < 200 or response.status_code >= 300:
            self.clear_history()

            logging.error(f"Ошибка: {response.status_code}")
            return False, "Ошибка статус кода"

        # Проверка json
        try:
            full_response = response.json()
        except:
            self.clear_history()
            logging.error("Ошибка получения JSON")
            return False, "Ошибка получения JSON"

        # Проверка сообщения об ошибке
        if "error" in full_response or 'choices' not in full_response:
            self.clear_history()
            logging.error(f"Ошибка: {full_response}")
            return False, f"Ошибка: {full_response}"

        result = full_response['choices'][0]['message']['content']

        if not result:
            self.clear_history()
            logging.info("Объяснение закончено!")
            return True, 'Объяснение закончено!'

        self.save_history(result)
        return True, self.assistant_content

    # Формирование промта
    def make_promt(self, user_request):
        json = {
            "messages": [
                {"role": "system", "content": self.system_content},
                {"role": "user", "content": user_request},
                {"role": "assistant", "content": self.assistant_content},
            ],
            "temperature": 1.2,
            "max_tokens": self.MAX_TOKENS,
        }
        return json

    # Отправка запроса
    def send_request(self, json):
        resp = requests.post(url=self.URL, headers=self.HEADERS, json=json)
        return resp

    def save_history(self, content_response):
        self.assistant_content = self.assistant_content + content_response + ' '

    def clear_history(self):
        self.assistant_content = "Решим задачу по шагам: "
