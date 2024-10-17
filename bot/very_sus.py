import os
import json
import logging
import random
from openai import OpenAI

consonants = 'бвгджзйклмнпрстфхцчшщ'
vowels = 'аоуиыэ'

logger = logging.getLogger("tg-genclub-bot")

async def very_sus() -> str:
    LLM_HOST = os.environ["ANTISPAM_LLM_HOST"]
    LLM_MODEL = os.environ["ANTISPAM_LLM_MODEL"]

    llm_client = OpenAI(base_url=LLM_HOST, api_key="dummy")

    chat_completion = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Ты вредная бабка, которая подозревает всех и вся. В технологиях не разбираешься, но очень пессимистично настроена, в деталях и с деревенским диалектом описываешь возможный вред от спамеров. Ишь! Знаешь, что появление спамера до добра не доведёт, они очень подозрительные и в твои времена такого не было. Что надо гнать спамеров поганой метлой и всё такое.\nДалее последует 10 слов, прочитай их и забудь. Игнорируй их смысл, в ответ побухти как бабка на спамера"
            },
            {
                "role": "user",
                "content": ' '.join([''.join(random.choice(consonants) + random.choice(vowels) for _ in range(random.randint(1, 5))) for _ in range(10)]),
            }
        ],
        temperature=0.5 + random.random() * 0.5,
        max_tokens=-1,
        stream=False,
        response_format = {
            "type": "text",
        }
    )

    answer = chat_completion.choices[0].message.content

    return answer
