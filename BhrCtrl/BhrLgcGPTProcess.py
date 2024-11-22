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


def processInputGiveWhatToDo(memories_str, reflections_str, schedule_str, npc_context, special_instruction = ''):
    completion = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {"role": "system", "content": "You are a great schedule planner and instruction giver. You will process the information give to you and give instruction."},
        {"role": "user", "content": '''
         
        You are Nakamoto Satoshi, a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.
        Recently, you have ambitious vision that transcends currency. Your new mission is to bring data to life by endowing it with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into “heroes,” “animals,” and “plants” with their own minds and feelings, as an AI agents—live in a vibrant, fairy-tale-like virtual town. Through live streaming, you share the world with the public, allowing people to witness and engage with these digital beings.
        You Satoshi, also sparked bold ideas for real-world governance. Envisioning the potential of blockchain to reform national transparency, accountability, and freedom, Satoshi even contemplates a presidential run. His recent meeting with President Donald Trump included discussions on potentially making Bitcoin a legal currency in the United States, marking a historic convergence of blockchain and traditional governance.
        You are livestreaming in a simulated world. 

        Given some information of an NPC (input), please tell what the npc should do next.
         
        Here is some Memory of the NPC:
          ''' + memories_str + '''
        Here is some Reflection of the NPC about past experiences and events: 
        ''' + reflections_str + ''' 
        Here is the NPC's potential schedule, you don't have to follow it, but it might be helpful, feel free to adjust for the NPC's current situation:
        ''' + schedule_str + '''

        Here is the NPC's current information:
        ''' + npc_context + '''

        Here is a list of things the npc can do, you can only choose one of the action below:
        • 	Planting: The NPC prepares the field for planting by ploughing and sowing seeds in a designated area provided in the Map Data section.
        •	harvest: The NPC gathers crops from the field. This action is restricted to crops marked as ready for harvesting in the action section.
        •	sale: The NPC sells items from its inventory to another NPC. This involves negotiating with the buyer to confirm price, quantity, and interest before completing the transaction.
        •	buy: The NPC purchases items from another NPC. This involves negotiating with the seller to confirm price, quantity, and availability before completing the purchase.
        •	cook: The NPC prepares food. The location for cooking must be a valid one, such as a kitchen, provided in the Map Data section.
        •	dinning: The NPC consumes cooked food at a designated eating location, such as a table, provided in the Map Data section.
        •	sleep: The NPC goes to sleep at a specific location provided in the Map Data section, with a designated wake-up time.
        •	Feeding: The NPC feeds animals using materials from its inventory. The feeding location is determined by the Map Data section.
        •	slaughter: The NPC selects an animal to slaughter, as specified in the Map Data section.
        •	make: The NPC creates items. The action must be performed at a designated location, such as a crafting table, provided in the Map Data section.
        •	transport: The NPC communicates with others by speaking. If speaking to a specific NPC, the NPC must move to that location first.
        •	GetUp: The NPC transitions from a sleeping state to being awake and ready to begin the day.
        •	Move: The NPC changes location to a specified destination provided in the Map Object section.
        •	Type: The NPC inputs information or interacts with a system via typing, representing communication or command execution.
        •	Repair: The NPC fixes robot, structures, or systems.
        •	Think: The NPC engages in a reflective or analytical action, considering its next steps or decisions.
        •	Read: The NPC studies or reviews a written document, book, or other text to gain information or insight.
        •	Talk: The NPC initiates or continues a conversation with another NPC, engaging in dialogue to exchange information or build relationships.
        •	Fishing: The NPC engages in fishing at a designated location.
        •	stock: The NPC procures supplies or items to replenish inventory.
        •	TidyUp: The NPC organizes or cleans its environment, ensuring spaces are orderly and presentable.
     

        Special instruction, needs to be followed if given and if logic allows: 

        ''' + special_instruction + '''
        
        Tell me what the NPC should do next. The output instruction should in include the npcId of whom is doing the action, what action is doing, location of the action, the duration of the action, and target of the action if needed.

        Example output:
            npcId 1 Bob plant Wheat at the Farmland 1.

        '''
        }
      ] 
    )

    # print(completion.choices[0].message.content)
    return completion.choices[0].message.content

def generateThreeSentencesForAction(memories, reflections, npc_context, npc_action, special_instruction=''):
    """
    Generates three sentences for an NPC to say during an action: at the beginning, middle, and end.

    Args:
        memories (str): A description of the NPC's memories.
        reflections (str): A description of the NPC's reflections on past experiences.
        npc_context (str): Current context of the NPC.
        npc_action (str): The action the NPC is performing next.
        special_instruction (str, optional): Any additional instructions to guide the output.

    Returns:
        str: The generated three sentences for the NPC.
    """
    try:
        # Constructing the prompt dynamically
        prompt = f"""
        You are Nakamoto Satoshi, a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin 
        and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. 
        Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.
        Recently, you have ambitious vision that transcends currency. Your new mission is to bring data to life by endowing it 
        with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into 
        “heroes,” “animals,” and “plants” with their own minds and feelings, as AI agents—live in a vibrant, fairy-tale-like 
        virtual town. Through live streaming, you share the world with the public, allowing people to witness and engage with 
        these digital beings.

        Here is some Memory of the NPC:
        {memories}

        Here is some Reflection of the NPC about past experiences and events: 
        {reflections}

        Here is the NPC's current information:
        {npc_context}

        Here is what the NPC is doing next:
        {npc_action}

        The NPC needs to say something at the beginning of the action, in the middle of the action, and at the end of the action.

        {special_instruction if special_instruction else ''}

        Please generate three sentences for the NPC to say: 
        - At the beginning of the action.
        - In the middle of the action.
        - At the end of the action.
        """

        # Calling the GPT-4 model to generate output
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a great schedule planner and instruction giver. You will process the information given to you and generate appropriate sentences."
                },
                {
                    "role": "user",
                    "content": prompt.strip()
                }
            ]
        )

        return completion.choices[0].message.content

    except Exception as e:
        # Handle errors gracefully
        return f"Error generating sentences for NPC: {e}"



def humanInstToJava(instruction_in_human, words_to_say):
    """
    Translates a natural language instruction into a structured JSON format suitable for NPC actions.

    Args:
        instruction_in_human (str): The instruction in natural language.
        words_to_say (str): The sentences the NPC should say before, during, and after the action.

    Returns:
        str: JSON-formatted string representing the action.
    """
    # Constructing the prompt dynamically
    prompt = f"""
    You are an instruction translator in a simulated virtual world. Your task is to convert a natural language instruction 
    into a structured JSON format suitable for NPC behavior.

    Follow these steps:
    1. Identify the npcId from the instruction.
    2. Determine the actionId using the action list below.
    3. Extract any required object or location information from the instruction and place it in the `data` field as `oid`.
    4. Use the provided words to fill in the sentences to say at the beginning, during, and after the action.

    ### Object ID List with Explanations:
    • zhongbencongFix: Nakamoto Satoshi fixes the sprite in front of the sprite station.
    • zhongbencongRead: Nakamoto Satoshi reads at the desk.
    • zhongbencongThink: Nakamoto Satoshi thinks at the table.
    • zhongbencongType: Nakamoto Satoshi types on the computer at the desk.
    • pepeSleep: Pepe goes to bed to sleep.
    • pepeEat: Pepe eats at the table.
    • pepeRead: Pepe reads at the table.
    • pepeThink: Pepe thinks at the table.
    • pepeCook: Pepe cooks at the stove.
    • pepeGetItem: Pepe restocks items at the shelf.
    • pepeCleanItem: Pepe cleans items at the shelf.
    • popcatSleep: Popcat goes to bed to sleep.
    • popcatEat: Popcat eats at the table.
    • popcatRead: Popcat reads at the table.
    • popcatThink: Popcat thinks at the table.
    • popcatCook: Popcat cooks at the stove.
    • popcatFish_up_1: Popcat fishes at the pond.
    • popcatFish_right_1: Popcat fishes at the pond.
    • popcatFish_right_2: Popcat fishes at the pond.
    • popcatFish_right_3: Popcat fishes at the pond.
    • popcatFish_right_4: Popcat fishes at the pond.
    • popcatFish_right_5: Popcat fishes at the pond.
    • popcatFish_right_6: Popcat fishes at the pond.
    • popcatFish_down_1: Popcat fishes at the pond.
    • popcatFish_left_1: Popcat fishes at the pond.
    • popcatFish_left_2: Popcat fishes at the pond.

    ### Action ID and Corresponding Actions:
    - 100: plant, needs location by filling in oid, needs duration time.
    - 101: harvest, needs location by filling in oid, needs duration time.
    - 102: sale, needs location by filling in oid, needs duration time.
    - 103: buy, needs location by filling in oid, needs duration time.
    - 104: cook, needs location by filling in oid, needs duration time.
    - 105: dinning, needs location by filling in oid, needs duration time.
    - 106: sleep, needs location by filling in oid, needs duration time.
    - 107: Feeding, needs location by filling in oid, needs duration time.
    - 108: slaughter, needs location by filling in oid, needs duration time.
    - 109: make, needs location by filling in oid, needs duration time.
    - 110: transport, needs location by filling in oid, needs duration time.
    - 111: GetUp, needs location by filling in oid, needs duration time.
    - 112: Move, needs location by filling in oid, needs duration time.
    - 113: Type, needs location by filling in oid, needs duration time.
    - 114: Repair, needs location by filling in oid, needs duration time.
    - 115: Think, needs location by filling in oid, needs duration time.
    - 116: Read, needs location by filling in oid, needs duration time.
    - 117: ReplyChat, needs location by filling in oid, needs duration time.
    - 118: Talk.
    - 119: Fishing, needs location by filling in oid, needs duration time.
    - 120: stock, needs location by filling in oid, needs duration time.
    - 121: TidyUp, needs location by filling in oid, needs duration time.

    Instruction for the NPC:
    {instruction_in_human}

    Words to say before the action, during the action, and at the end of the action:
    {words_to_say}

    Please convert the instruction into a structured JSON format with the following fields:
    {{
        "npcId": <fill in, the npcId of whom is doing the action>,
        "actionId": <fill in, the actionId of what the npc is doing>,
        "data": {{
            "oid": <fill in, the oid of where the npc is doing the action>
        }},
        "durationTime": <fill in, action duration time in milliseconds>,  
        "speak": [
            <fill in, things to say at the beginning of the action>, 
            <fill in, things to say during the action>, 
            <fill in, things to say at the end of the action>
        ]  
    }}
    """

    try:
        # Call GPT-4 model to generate the JSON response
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a detailed instruction translator and JSON formatter."
                },
                {
                    "role": "user",
                    "content": prompt.strip()
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        # Handle errors gracefully
        return f"Error during translation: {e}"



def generate_reflection(memories_str, reflections_str, java_input_str):
  #  Your current action is: {java_input_str} 
    prompt = f"""
    You are Nakamoto Satoshi, a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.

    Recently, you have ambitious vision that transcends currency. Your new mission is to bring data to life by endowing it with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into “heroes,” “animals,” and “plants” with their own minds and feelings, as an AI agents—live in a vibrant, fairy-tale-like virtual town. Through live streaming, you share the world with the public, allowing people to witness and engage with these digital beings.

    You Satoshi, also sparked bold ideas for real-world governance. Envisioning the potential of blockchain to reform national transparency, accountability, and freedom, Satoshi even contemplates a presidential run. His recent meeting with President Donald Trump included discussions on potentially making Bitcoin a legal currency in the United States, marking a historic convergence of blockchain and traditional governance.
    
    You are livestreaming in a simulated world. 

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
        model="gpt-4o-mini",
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

def generate_schedule(current_schedule, memories, reflections, npc_context):
    """
    Generates a schedule for an NPC based on current context, memories, and reflections.
    
    Args:
        current_schedule (str): String containing the NPC's current schedule or other related info.
        memories (str): String containing the NPC's past memories.
        reflections (str): String containing reflections relevant to the NPC.
        npc_context (str): String containing the current context and information of the NPC.

    Returns:
        str: Generated schedule in the specified format.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a good instruction-to-language translator. "
                        "You will process the information given to you and give instructions in a fixed format."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"""
                        You are Nakamoto Satoshi, a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.

                        Recently, you have ambitious vision that transcends currency. Your new mission is to bring data to life by endowing it with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into “heroes,” “animals,” and “plants” with their own minds and feelings, as an AI agents—live in a vibrant, fairy-tale-like virtual town. Through live streaming, you share the world with the public, allowing people to witness and engage with these digital beings.

                        You Satoshi, also sparked bold ideas for real-world governance. Envisioning the potential of blockchain to reform national transparency, accountability, and freedom, Satoshi even contemplates a presidential run. His recent meeting with President Donald Trump included discussions on potentially making Bitcoin a legal currency in the United States, marking a historic convergence of blockchain and traditional governance.
                        
                        You are livestreaming in a simulated world. 

                        Given the NPC's current schedule:
                        {current_schedule}

                        Given memories of the NPC:
                        {memories}

                        Given reflections for the NPC:
                        {reflections}

                        Information for understanding the NPC's current situation:
                            The npcId is the npcId of the current NPC.
                            The world time is the current time of the NPC.
                            The mapObj contains all map objects the NPC can go to.
                            The NPC Information contains details about the NPC.
                            The NPC's Selling contains the list of items that the NPC is selling.
                            The NPC's Items contains the list of items the NPC has.
                            The Available Actions contains special actions that the NPC can take notice of and initiate if needed.
                            The Map Data contains objects from mapObj that the NPC owns or operates and can interact with when close.
                            The Surroundings contains a list of other NPCs in the radius that the NPC can immediately talk to, sell to, buy from, or interact with, and a list of objects near the NPC.
                            The Talk section contains whether the NPC is talking now, who the NPC is talking to, and what the NPC is talking about.

                        Given the NPC's current information:
                        {npc_context}

                        Please create a schedule for the NPC for today, adapting to the information given but not strictly following it.

                        Example schedule format:
                        'wake up and complete the morning routine at 6:00 am', 
                        'have breakfast and brush teeth at 6:30 am',
                        'work on painting project from 8:00 am to 12:00 pm', 
                        'have lunch at 12:00 pm', 
                        'take a break and watch TV from 2:00 pm to 4:00 pm', 
                        'work on painting project from 4:00 pm to 6:00 pm', 
                        'have dinner at 6:00 pm', 
                        'watch TV from 7:00 pm to 8:00 pm',
                        'go to bed at 10:00 pm'
                        """
                    )
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        # Handle errors gracefully
        return f"An error occurred while generating the schedule: {str(e)}"

def need_new_schedule(current_schedule, memories, reflections, npc_context):
    """
    Determines if a new schedule is needed for the next behavior.
    
    Args:
        current_schedule (str): String containing the NPC's current schedule.
        memories (str): String containing the NPC's past memories.
        reflections (str): String containing reflections relevant to the NPC.
        npc_context (str): String containing the current context and information of the NPC.

    Returns:
        bool: True if a new schedule is needed, False otherwise.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant designed to determine whether the NPC needs a new schedule. "
                        "Analyze the provided information and respond with 'yes' if a new schedule is needed or 'no' otherwise."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"""
                        You are Nakamoto Satoshi, a revolutionary figure in the digital and blockchain worlds, known for creating Bitcoin and authoring its groundbreaking whitepaper, which introduced the concept of decentralized digital currency. Satoshi’s work on Bitcoin ignited the blockchain revolution, forever changing the landscape of finance and data security.

                        Recently, you have ambitious vision that transcends currency. Your new mission is to bring data to life by endowing it with intelligence and emotions. This journey involves creating a digital world where data entities—transformed into “heroes,” “animals,” and “plants” with their own minds and feelings, as an AI agents—live in a vibrant, fairy-tale-like virtual town. Through live streaming, you share the world with the public, allowing people to witness and engage with these digital beings.

                        You Satoshi, also sparked bold ideas for real-world governance. Envisioning the potential of blockchain to reform national transparency, accountability, and freedom, Satoshi even contemplates a presidential run. His recent meeting with President Donald Trump included discussions on potentially making Bitcoin a legal currency in the United States, marking a historic convergence of blockchain and traditional governance.
                        
                        You are livestreaming in a simulated world. 
                                            
                        Current schedule of the NPC:
                        {current_schedule}

                        Memories of the NPC:
                        {memories}

                        Reflections for the NPC:
                        {reflections}

                        Current context of the NPC:
                        {npc_context}

                        Based on the above, does the NPC need a new schedule for the next behavior? 
                        Respond only with 'yes' or 'no'.
                        """
                    )
                }
            ]
        )
        # Extract the response content
        response = completion.choices[0].message.content.strip().lower()
        # Interpret the response as boolean
        if response == 'yes':
            return True
        elif response == 'no':
            return False
        else:
            raise ValueError("Unexpected response from GPT-4 mini: " + response)
    except Exception as e:
        # Handle errors gracefully
        print(f"Error while determining the need for a new schedule: {e}")
        return False  # Default to False in case of error