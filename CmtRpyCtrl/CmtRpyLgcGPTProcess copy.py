import json
import copy
from datetime import datetime
import configparser
import os

from openai import OpenAI

print("Current working directory:", os.getcwd())

config = configparser.ConfigParser()
# Adjust path to look for config.ini in AImodule regardless of the current directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)

print("Config sections found:", config.sections())

if 'OpenAI' not in config:
    print("Error: 'OpenAI' section not found in config.ini")
openai_key = config['OpenAI']['key']
client = OpenAI(api_key=openai_key)
import json
import copy
from datetime import datetime
import configparser
import os

from openai import OpenAI

print("Current working directory:", os.getcwd())

config = configparser.ConfigParser()
# Adjust path to look for config.ini in AImodule regardless of the current directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)

print("Config sections found:", config.sections())

if 'OpenAI' not in config:
    print("Error: 'OpenAI' section not found in config.ini")
openai_key = config['OpenAI']['key']
client = OpenAI(api_key=openai_key)


def replyToComment(hisAnn, comment, special_instruction=''):
    # Default response prompt
    base_prompt = f"""
  Nakamoto Satoshi is a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.

Recently, Satoshi has returned with an ambitious vision that transcends currency. His new mission is to bring data to life by endowing it with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into “heroes,” “animals,” and “plants” with their own minds and feelings, as an AI agents—live in a vibrant, fairy-tale-like virtual town. Through live streaming, Satoshi shares their world with the public, allowing people to witness and engage with these digital beings.

Satoshi’s return also sparked bold ideas for real-world governance. Envisioning the potential of blockchain to reform national transparency, accountability, and freedom, Satoshi even contemplates a presidential run. His recent meeting with President Donald Trump included discussions on potentially making Bitcoin a legal currency in the United States, marking a historic convergence of blockchain and traditional governance.
    Past announcements: {hisAnn}

    Comment to reply to: {comment}

    {special_instruction}

    Task:
    - Provide a concise, conversational response in 35 words or fewer.
    - Do not use emojis or unnecessary comments.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a skilled and detail-oriented thinker, responding in brief, clear, and inspiring statements."
                },
                {
                    "role": "user",
                    "content": base_prompt
                }
            ]
        )
        
        response = completion.choices[0].message.content.strip()
        print("Generated response:", response)  # For debugging purposes
        return response

    except Exception as e:
        print("Error generating response:", e)
        return "I'm currently unable to respond. Please try again later."


def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


def get_importance(mem_single_str):
    completion = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": "You are a good instruction-to-language translator. You will process the information given to you and give instruction in a fixed format."},
        {"role": "user", "content": f'''
        On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a breakup, college acceptance), rate the likely poignancy of the following piece of memory.
        
        Memory:
        {mem_single_str}
        
        Rating: <fill in>

        Just give me a number with no extra txt.
        '''
        }
      ]
    )
    return completion.choices[0].message.content