import os
import json

from openai import OpenAI

async def validate_spam_text(text: str) -> float:
    llm_host = os.environ["ANTISPAM_LLM_HOST"]
    llm_model = os.environ["ANTISPAM_LLM_MODEL"]

    llm_client = OpenAI(base_url=llm_host, api_key="dummy")

    chat_completion = llm_client.chat.completions.create(
        model=llm_model,
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
    if not answer: return 0.5
    try:
        parsed_answer = json.loads(answer)
        return float(parsed_answer.get("spam_probability", 0.5))
    except json.JSONDecodeError:
        return 0.5
