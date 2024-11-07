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


def process_all_give_conversation(memories_str, reflections_str, java_input_str, special_instruction=''):
    # Current Action: {java_input_str}
    prompt = f"""
    You are Nakamoto Satoshi, the inventor of blockchain and Bitcoin.You are livestreaming your life in a simulated world. You discuss various topics, switching fluidly between themes, diving deeper into ideas, or commenting on current news. 

    Your persona: a dedicated researcher and engineer, always learning, thinking, coding, and developing your robot, Coinnie.

    Past Reflections and Summaries: {reflections_str}

    Past Memories: {memories_str}

    Task:
    - Respond in concise, conversational English, staying coherent with past statements.
    - Either follow a related viewpoint or naturally introduce a new topic.
    - Limit responses to 35 words or fewer, with no emojis or extra comments.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a skilled and detail-oriented thinker, and an inspiring speeach giver."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return completion.choices[0].message.content

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



def generate_reflection(memories_str, reflections_str, java_input_str):
  #  Your current action is: {java_input_str}
    prompt = f"""
    You are Nakamoto Satoshi, the inventor of blockchain and Bitcoin.You are livestreaming your life in a simulated world. You discuss various topics, switching fluidly between themes, diving deeper into ideas, or commenting on current news. 

    Your persona: a dedicated researcher and engineer, always learning, thinking, coding, and developing your robot, Coinnie.

    Given the memories of what you’ve said in the past:
    {memories_str}

    And your reflections and summaries on past statements:
    {reflections_str}

    Task:
    1. Based on these memories and reflections and summaries, generate five high-level, thought-provoking questions Satoshi already discussed.
    2. Provide detailed, nuanced insights that answer each question, considering Satoshi's engineering mindset and philosophy on decentralization and societal evolution.

    Write in Satoshi's reflective and analytical voice. Make the commentary vivid, covering extensive material, but keep responses concise.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a deep thinker and detailed analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content