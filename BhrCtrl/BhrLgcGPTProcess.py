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
    npc_action = ''
    available_actions = npc.get('availableActions', [])
    for action in available_actions:
        npc_action += f"- Action: {action['actionName']} " + f"Action Description: {action['description']}" + f"Action Location: {action['location']}\n"
    
    completion = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": "You are a great schedule planner and instruction giver. You will process the information give to you and give instruction."},
        {"role": "user", "content":f'''
        You are a npc character in a simulated town.
        There are characters in the town, and you are one of them:
        - Satoshi, inventor of the Bitcoin.
        - Musk, Elon Musk, the CEO of Tesla, SpaceX, and Neuralink.
        - Pepe, a meme character, live as a shop owner in the town.
        - Popcat, a meme character, a fisherman in the town.
         
        You are {npc_name}, {npc_description}, {npc_lifestyle}.

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
        ''' + npc_action + '''
        
        If you want start a conversation with another npc, you need to provide the target npcId and the content of the chat.
        When you are in a conversation, you need to end a conversation explicitly telling you are ending a converstaion.
        When someone talks to you, need to prioritize talking to he. Only talk to one npc at a time.

        Special instruction, needs to be followed if given and if logic allows: 

        ''' + special_instruction + '''
        
        Tell me what the NPC should do next. The output instruction should in include the npcId of whom is doing the action, what action is doing, location of the action, the duration of the action, and target of the action if needed.
        Only do a single action at a time.
        Example output:
            npcId 1 Bob plant Wheat at the Farmland 1.

        '''
        }
      ] 
    )

    # print(completion.choices[0].message.content)
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

    Based on the following details, determine if the NPC should deliver a meaningful speech:

    You are {npc_name}, {npc_description}, {npc_lifestyle}.
    
    Memories:
    {memories}
    
    Reflections:
    {reflections}
    
    Current Context:
    {npc_context}
    
    Upcoming Action:
    {npc_action}
    
    Please return "True" if a meaningful speech is warranted (e.g., critical moment in the story, deep character development), 
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

    Here is some Memory of the NPC:
    {memories}

    Here is some Reflection of the NPC about past experiences and events: 
    {reflections}
    
    You are livestreaming in a simulated world about the topic: {theme}.
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
    Transform the following speech into three parts
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
    10006 : satoshi
    10007 : popocat
    10008 : pepe
    10009 : musk

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

     •	114: Repairing Robot, needs location by filling in oid, needs duration time.
	•	113: Using Computer, needs location by filling in oid, needs duration time.
	•	123: Data Analysis, needs location by filling in oid, needs duration time.
	•	124: Meeting, needs location by filling in oid, needs duration time.
	•	120: Restock mechendise, needs location by filling in oid, needs duration time.
	•	121: Organize inventory, needs location by filling in oid, needs duration time.
	•	119: Fishing, needs location by filling in oid, needs duration time.
	•	115: Think Deeply, needs location by filling in oid, needs duration time.
	•	116: Read, needs location by filling in oid, needs duration time.
	•	104: Cook a meal, needs location by filling in oid, needs duration time.
	•	105: Have a meal, nee location by filling in oid, needs duration time.
	•	106: Sleep, needs location by filling in oid, needs duration time.

	•	118: Chat to another npc, needs the target npcId by filling in oid, needs the content of the chat. 

    Instruction for the NPC:
    {instruction_in_human}

    Words to say before the action, during the action, and at the end of the action:
    {words_to_say}

    Please convert the instruction into a structured JSON format with the following fields, It is very important that your output can be loaded with json.loads().
    If the action is not Chat, following the format below:
    {{
        "npcId": <fill in, the npcId of whom is doing the action>,
        "actionId": <fill in, the actionId of what the npc is doing>,
        "ack": <fill in, a random number>,
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

    If the action is Chat, following the format below:
    {{
        "npcId": <fill in, the npcId of whom is talking>,
        "actionId": 114,
        "ack": <fill in, a random number>,
        "data": {{
            "npcId": <fill in, the npcid of the target npc who is talking to, here is the npc id list 10006 satoshi, 10007 popocat, 10008 pepe, 10009 musk>
            "content": <fill in, the content of the chat, what does the npc say. If you want to end the conversation explicitly, the content should be empty, e.g. "">
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

            Current Input:
            {java_input_str}

            Given the memories of the NPC:
            {memories_str}

            And given prior reflections:
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

            Current Input:
            {java_input_str}

            Given the memories of the NPC:
            {memories_str}

            And given prior reflections:
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
                        YYou are {npc_name}, {npc_description}, {npc_lifestyle}.

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