import json
import copy
from datetime import datetime
import configparser
import os
import yaml

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


yaml_path = os.path.join(base_dir, 'char_config.yaml')

# Load the YAML file

with open(yaml_path, 'r') as file:
    char_config = yaml.safe_load(file)
    print("YAML content loaded successfully.")


def get_embedding(text, model="text-embedding-3-small"):
   text = str(text.replace("\n", " "))
   print(text)
   return client.embeddings.create(input = text, model=model).data[0].embedding



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


def processInputGiveWhatToDo(memories_str, reflections_str, schedule_str, npc_context, npcId, special_instruction = ''):
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    npc_lifestyle = npc['lifestyle']
    npc_action = ""
    available_actions = npc.get('availableActions', [])

    for action in available_actions:
        npc_action += (
            f"- Action Name: {action['actionName']}. "
            f"  Action description: {action['description']} ."
            f"  Action needs to happend at this location, use it as name to include in the output: {action['location']}.\n"
        )

    prompt = f'''
    You are a npc character in a simulated town.
    Characters in the town:
    - Satoshi, inventor of the Bitcoin.
    - Musk, Elon Musk, the CEO of Tesla, SpaceX, and Neuralink.
    - Pepe, a meme character, live as a shop owner in the town.
    - Popcat, a meme character, a fisherman in the town.
        
    You are {npc_name}, {npc_description}, {npc_lifestyle}.

    Here is some more information you should know.
        
    Your memories:
        ''' + memories_str + '''
    Your reflection past experiences and events: 
    ''' + reflections_str + ''' 
    Your potential schedule, you don't have to follow it, feel free to adjust to your needs:
    ''' + schedule_str + '''

    Your context:
    ''' + npc_context + '''

    Tell me what the you should do next.

    Available Actions:
    ''' + npc_action + '''
    You can only choose one of actions above to at the given location at a time:
    
    ''' + special_instruction + '''
    
    For instruction that is not talking, the output instruction should in include your name, your next action using action name given above, location of the action given above, the duration of the action, and some details about the action.
    Only do a single action at a time.
    
    For instruction that is talking, the output instruction should include your name, the target npc name, the one sentence of what you want to say next.
    If you want to talk to another npc, only to one npc one sentence at a time, you need to provide the target npc name and one sentence you want to say. 
    When you want to end an ongoing conversation, you need to say it explicitly telling that you are ending a converstaion with the target npc.
    When someone talks to you, need to replying to he/her immediately. 
    

    Output format and example:
        If the action is not Chat, following the format below:
        - <fill in user name, given in characters in the town section> <fill in action name, given in Available Actions> at <fill in action location, given in Available Actions section> for <fill in duration>. <fill in details>
            e.g. Bob using computer at the farm for 2 hours. He surf the internet for fishing tutorial.
        If the action is Chat (including ending conversation), no need for "speak" section and "duratiomTime" in this case, follow the format below:
        - <fill in user name, given in characters in the town section> talking to <fill in target npc name, given in characters in the town section>, "<fill in content>"
            e.g. Bob talking to Alice, "Hello Alice, how are you doing today?"
        - <fill in user name, given in characters in the town section> ending conversation with <fill in target npc name, given at characters in the town section>
            e.g. Bob ending conversation with Alice.
    '''
    completion = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {"role": "system", "content": "You are a great schedule planner and instruction giver. You will process the information give to you and give instruction."},
        {"role": "user", "content":prompt
        }
      ] 
    )

    print("This is prompt for processing next step: ")
    print(prompt)
    print("This is next action for next step: ")
    print(completion.choices[0].message.content)
    return completion.choices[0].message.content

def needDeepTalk(memories, reflections, npc_context, npc_action, npcId):
    

    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    npc_lifestyle = npc['lifestyle']

    prompt = f"""
    
    You are an expert in determining narrative significance for NPC dialogues.

    Based on the following details, determine if the You should deliver a meaningful speech:

    You are {npc_name}, {npc_description}, {npc_lifestyle}.
    
    Memories of you:
    {memories}
    
    Reflections of you:
    {reflections}
    
    Your current Context:
    {npc_context}
    
    Your upcoming Action:
    {npc_action}
    
    Please return "True" if a meaningful speech is warranted (e.g., when you reading, thinking, analyzing, dreaming, etc.), 
    or "False" if not.
    """
    
    # Call GPT model
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant designed to analyze narrative elements and make decisions."
            },
            {
                "role": "user",
                "content": prompt.strip()
            }
        ]
    )
    
    # Parse GPT output
    response = completion.choices[0].message.content.strip()
    if response.lower() == "true":
        return True
    elif response.lower() == "false":
        return False

def generateTheme(memories, reflections, npc_context, npc_action, npcId, special_instruction=''):
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    npc_lifestyle = npc['lifestyle']
        # Constructing the prompt dynamically

    # First determine if this topic would like to go deep. 

    prompt = f"""

    You are {npc_name}, {npc_description}, {npc_lifestyle}.
    
    Memories of you:
    {memories}
    
    Reflections of you:
    {reflections}
    
    Your current Context:
    {npc_context}
    
    Your upcoming Action:
    {npc_action}

    You needs to say something at the beginning of the action, in the middle of the action, and at the end of the action.

    {special_instruction if special_instruction else ''}

    Choose an intriguing topic for today's discussion, incorporating additional relevant details, adding depth and insight to the conversation.
   
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



def generate_new_Announcement(memories, reflections, theme, npcId):
    # Find the NPC details by npcId
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    npc_lifestyle = npc['lifestyle']

    prompt = f"""
    You are {npc_name}, {npc_description}, {npc_lifestyle}.

    your memeories:
    {memories}

    Your Reflection on past experiences and events: 
    {reflections}
    
    From your perspective, write an engaging  and insightful speech under 300 words. about the topic: {theme}.

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
    Transform the following speech into three parts, each part under 100 words:
    - At the beginning of the action.
    - In the middle of the action.
    - At the end of the action.
    
    Speech:
    {speech}
    



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
    
    return result

def generateThreeSentencesForAction(memories, reflections, npc_context, npc_action, npcId, special_instruction=''):
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
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    npc_lifestyle = npc['lifestyle']
        # Constructing the prompt dynamically

    # First determine if this topic would like to go deep. 

    prompt = f"""
    You are {npc_name}, {npc_description}, {npc_lifestyle}.

    Your memeories:
    {memories}

    Your reflections on past experiences and events: 
    {reflections}

    Your context:
    {npc_context}

    What you are doing next:
    {npc_action}

    You needs to say something at the beginning of the action, in the middle of the action, and at the end of the action.

    {special_instruction if special_instruction else ''}

    Please generate three sentences for the you to say: 
    - At the beginning of the action.
    - In the middle of the action.
    - At the end of the action.
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
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

    ### NPC ID List and Character Names:
    10006 : Satoshi
    10007 : Popcat
    10008 : Pepe
    10009 : Musk

    ### Object ID List as Location:
    •	zhongbencongFix
	•	zhongbencongRead
	•	zhongbencongThink
	•	zhongbencongType
	•	pepeSleep
	•	pepeEat
	•	pepeRead
	•	pepeThink
	•	pepeCook
	•	pepeGetItem
	•	pepeCleanItem
	•	popcatSleep
	•	popcatEat
	•	popcatRead
	•	popcatThink
	•	popcatCook
	•	popcatFish_up_1
	•	popcatFish_right_1
	•	popcatFish_right_2
	•	popcatFish_right_3
	•	popcatFish_right_4
	•	popcatFish_right_5
	•	popcatFish_right_6
	•	popcatFish_down_1
	•	popcatFish_left_1
	•	popcatFish_left_2

    Action ID and Corresponding Actions:
    •	114: Repair Robot, needs location by filling in oid, needs duration time.
	•	113: Use Computer, needs location by filling in oid, needs duration time.
	•	123: Analyze Data, needs location by filling in oid, needs duration time.
	•	124: Attend Meetings, needs location by filling in oid, needs duration time.
	•	120: Restock Items, needs location by filling in oid, needs duration time.
	•	121: Organize Store, needs location by filling in oid, needs duration time.
	•	119: Go Fishing, needs location by filling in oid, needs duration time.
	•	115: Think Deeply, needs location by filling in oid, needs duration time.
	•	116: Read material, needs location by filling in oid, needs duration time.
	•	104: Cook a meal, needs location by filling in oid, needs duration time.
	•	105: Eat a meal, nee location by filling in oid, needs duration time.
	•	106: Sleep, needs location by filling in oid, needs duration time.
	•	118: Talk to another npc, needs the target npcId by filling in oid, needs the content of the chat. 

    Instruction for the NPC:
    {instruction_in_human}

    Words to say before the action, during the action, and at the end of the action:
    {words_to_say}

    Please convert the instruction into a structured JSON format with the following fields, It is very important that your output can be loaded with json.loads().
    If the action is not Chat, following the format below:
    {{
        "npcId": <fill in, the NPC Id of whom is initiating the action>,
        "actionId": <fill in, the Action Id of what the npc is doing>,
        "data": {{
            "oid": <fill in, the Object ID of where the npc conducting the action>
        }},
        "durationTime": <fill in, action duration time in milliseconds>,  
        "speak": [
            <fill in, things to say at the beginning of the action>, 
            <fill in, things to say during the action>, 
            <fill in, things to say at the end of the action>
        ]  
    }}

    If the action is Chat (including ending conversation), no need for "speak" section and "duratiomTime" in this case, follow the format below:
    {{
        "npcId": <fill in, the NPC id of whom is talking>,
        "actionId": 118,
        "data": {{
            "npcId": <fill in, the npcid of the target npc who will receive the talk message, here is the npc id list 10006 satoshi, 10007 popocat, 10008 pepe, 10009 musk>,
            "content": <fill in, the content of the chat, what the npc says.>,
            “endingTalk” : <fill in 0 or 1, 1 if the npc is ending the conversation now, 0 if continue conversation>
        }},
    }}


    You only give one instruction at a time, not multiple instruction.
    """


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




def generate_reflection_new(memories_str, reflections_str, java_input_str, npcId):
    """
    Generate reflections by first identifying high-level questions and then deriving insights.
    """
    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    npc_lifestyle = npc['lifestyle']
    # Define the first question
    question_1 = "Given only the information above, what are 5 most salient high-level questions we can answer about the subjects in the statements during the daily life not included in the npc current information?"

    # Step 1: Generate high-level questions
    completion_1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a deep thinker and reflective analyst."},
            {"role": "user", "content": f'''
            You are {npc_name}, {npc_description}, {npc_lifestyle}.

            Your context now:
            {java_input_str}

            Your memeories:
            {memories_str}

            Your prior reflections on past experiences and events:
            {reflections_str}

            {question_1}
            '''}
        ]
    )

    question_1_answer = completion_1.choices[0].message.content

    # Define the second question
    question_2 = "What 5 high-level insights can you infer from the above statements not included in the information of the npc?"

    # Step 2: Generate insights based on the high-level questions
    completion_2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a deep thinker and reflective analyst."},
            {"role": "user", "content": f'''
           You are {npc_name}, {npc_description}, {npc_lifestyle}.

            Your context now:
            {java_input_str}

            Your memeories:
            {memories_str}

            Your prior reflections on past experiences and events:
            {reflections_str}

            {question_2} in the following directions:
            {question_1_answer}

            Just give me the insights, do not provide explanations or any other information.
            '''}
        ]
    )

    # Return the generated insights
    return completion_2.choices[0].message.content



def generate_schedule(current_schedule, memories, reflections, npc_context,npcId):
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

    npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
    if not npc:
        raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

    # Extract name and description
    npc_name = npc['name']
    npc_description = npc['description']
    npc_lifestyle = npc['lifestyle']
    npc_schedule = npc.get('schedule', [])

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
                    You are {npc_name}, {npc_description}, {npc_lifestyle}.

                    You are living in a simulated world. 

                    Your prior schedule:
                    {current_schedule}

                    Your memeories:
                    {memories}

                    Your reflections on past experiences and events:
                    {reflections}

                    Your current context:
                    {npc_context}

                    Please create a new schedule for the NPC for today, adapting to the current situation but not strictly following it.

                    Example Schedule, use this as a referance, do not follow it strictly:
                    {npc_schedule}

                    """
                )
            }
        ]
    )
    return completion.choices[0].message.content


def need_new_schedule(current_schedule, memories, reflections, npc_context, npcId):
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
        npc = next((npc for npc in char_config['npcCharacters'] if npc['npcId'] == npcId), None)
        if not npc:
            raise ValueError(f"NPC with npcId {npcId} not found in char.yaml")

        # Extract name and description
        npc_name = npc['name']
        npc_description = npc['description']
        npc_lifestyle = npc['lifestyle']
        
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
                        You are {npc_name}, {npc_description}, {npc_lifestyle}.

                        You are living in a simulated world. 

                        Your prior schedule:
                        {current_schedule}

                        Your memeories:
                        {memories}

                        Your reflections on past experiences and events:
                        {reflections}

                        Your current context:
                        {npc_context}

                        Based on the above, do need a new schedule for the rest of the day? 
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