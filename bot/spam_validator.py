import os
import json
import logging

from openai import OpenAI
from banned_words import contains_banned_texts

logger = logging.getLogger("tg-genclub-bot")

async def validate_spam_text(text: str) -> float:
    if contains_banned_texts(text):
        return 1.1
    else:
        return await validate_spam_text_llm(text)

async def validate_spam_text_llm(text: str) -> float:
    LLM_HOST = os.environ["ANTISPAM_LLM_HOST"]
    LLM_MODEL = os.environ["ANTISPAM_LLM_MODEL"]

    llm_client = OpenAI(base_url=LLM_HOST, api_key="dummy")

    chat_completion = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Ты антиспам система, которая просматривает сообщение и вычисляет вероятность того, что сообщение является спамом. Когда пользователь предоставит тебе текст, тебе нужно выдать вероятность того, что этот текст спам. Вероятность это число с плавающей точкой от 0 до 1. 0 если сообщение не спам, 1 если это сообщение спам. Далее идет сообщение для проверки:"
            },
            {
                "role": "user",
                "content": "<message_to_validate>" + str(text) + "</message_to_validate>"
            }
        ],
        temperature=0.5,
        max_tokens=-1,
        stream=False,
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "spam_detection",
                "strict": "true",
                "schema": {
                    "type": "object",
                    "properties": {
                        "spam_probability": {
                            "type": "number"
                        }
                    },
                    "required": [
                        "spam_probability"
                    ]
                }
            }
        }
    )

    answer = chat_completion.choices[0].message.content
    if not answer:
        logging.debug(f"no valid response from LLM")
        return 0.5
    try:
        parsed_answer = json.loads(answer)
        return float(parsed_answer.get("spam_probability", 0.5))
    except Exception as e:
        logging.debug(f"error while unwrapping answer: {answer} +++ {e}")
        return 0.5
