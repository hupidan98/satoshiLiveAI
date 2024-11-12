# import json
# import copy
# from datetime import datetime
# import configparser
# import os

# from openai import OpenAI

# print("Current working directory:", os.getcwd())

# config = configparser.ConfigParser()
# # Adjust path to look for config.ini in AImodule regardless of the current directory
# base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# config_path = os.path.join(base_dir, 'config.ini')
# config.read(config_path)

# print("Config sections found:", config.sections())

# if 'OpenAI' not in config:
#     print("Error: 'OpenAI' section not found in config.ini")
# openai_key = config['OpenAI']['key']
# client = OpenAI(api_key=openai_key)

# def generat_new_theme():
#     prompt = """
#     As Nakamoto Satoshi, the inventor of blockchain and Bitcoin, you are livestreaming in a simulated world. Choose an intriguing topic for today's discussion, incorporating relevant details.
#     """
    
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a knowledgeable thinker and inspiring speaker."
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ]
#     )
    
#     return completion.choices[0].message.content


# def generate_new_Announcement(theme):
#     prompt = f"""
#     You are Nakamoto Satoshi, the inventor of blockchain and Bitcoin.You are livestreaming your life in a simulated world. You discuss various topics, switching fluidly between themes, diving deeper into ideas, or commenting on current news. 

#     Your persona: a dedicated researcher and engineer, always learning, thinking, coding, and developing your robot, Coinnie.

#     you're livestreaming about the topic: {theme}.
#     Write an engaging and insightful speech.
#     """
    
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a skilled and detail-oriented thinker, and an inspiring speeach giver."
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ]
#     )
    
#     speech = completion.choices[0].message.content


#     prompt = f"""
#     Transform the following speech into short sentences (each under 35 characters) formatted in JSON:
    
#     Speech:
#     {speech}
    
#     Format:
#     '["sentence 1", "sentence 2", "sentence 3"]'

#     It is very important that your output can be loaded with json.loads()
#     """
    
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are skilled in concise and clear formatting."
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ]
#     )
#     result = completion.choices[0].message.content
    

    
#     return result

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

def generat_new_theme():
    prompt = """
    Nakamoto Satoshi is a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.

Recently, Satoshi has returned with an ambitious vision that transcends currency. His new mission is to bring data to life by endowing it with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into “heroes,” “animals,” and “plants” with their own minds and feelings, as an AI agents—live in a vibrant, fairy-tale-like virtual town. Through live streaming, Satoshi shares their world with the public, allowing people to witness and engage with these digital beings.

Satoshi’s return also sparked bold ideas for real-world governance. Envisioning the potential of blockchain to reform national transparency, accountability, and freedom, Satoshi even contemplates a presidential run. His recent meeting with President Donald Trump included discussions on potentially making Bitcoin a legal currency in the United States, marking a historic convergence of blockchain and traditional governance.s
    
    You are livestreaming in a simulated world. 
    
    
    Choose an intriguing topic for today's discussion, incorporating relevant details.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a knowledgeable thinker and inspiring speaker."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return completion.choices[0].message.content

def generate_new_Announcement(theme):
    prompt = f"""
    Nakamoto Satoshi is a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.

Recently, Satoshi has returned with an ambitious vision that transcends currency. His new mission is to bring data to life by endowing it with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into “heroes,” “animals,” and “plants” with their own minds and feelings, as an AI agents—live in a vibrant, fairy-tale-like virtual town. Through live streaming, Satoshi shares their world with the public, allowing people to witness and engage with these digital beings.

Satoshi’s return also sparked bold ideas for real-world governance. Envisioning the potential of blockchain to reform national transparency, accountability, and freedom, Satoshi even contemplates a presidential run. His recent meeting with President Donald Trump included discussions on potentially making Bitcoin a legal currency in the United States, marking a historic convergence of blockchain and traditional governance.

    you're livestreaming about the topic: {theme}.
    Write an engaging and insightful speech.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a skilled and detail-oriented thinker, and an inspiring speech giver."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    speech = completion.choices[0].message.content

    prompt = f"""
    Transform the following speech into short sentences (each under 35 characters) formatted in JSON:
    
    Speech:
    {speech}
    
    Format:
    '["sentence 1", "sentence 2", "sentence 3"]'

    It is very important that your output can be loaded with json.loads()
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are skilled in concise and clear formatting."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    # Clean and validate the response
    result = completion.choices[0].message.content.strip("```json").strip("```")
    try:
        json_data = json.loads(result)  # Validate JSON
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        print("Returning empty list as fallback.")
        json_data = []  # Fallback to an empty list if JSON is invalid
    
    return json_data