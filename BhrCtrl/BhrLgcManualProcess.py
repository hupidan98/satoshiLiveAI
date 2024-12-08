import json
from datetime import datetime

def parse_npc_info_for_nextaction(json_input):

    try:
        # Load the JSON data
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"
    
    # Extract world time and convert from milliseconds to a readable format
    world_time_ms = data.get('world', {}).get('time', 0)
    try:
        world_time = datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
    except (OSError, ValueError):
        world_time = "Invalid world time"
    talk_info, is_talking = parse_talking_from_java(json_input)
    # action_info = parse_cur_action_from_java(json_input) 
    output_text = f'''
    Now is {world_time}. 
    {talk_info}
    '''

    return output_text


# def parse_cur_action_from_java(json_input):

#     try:
#         # Load the JSON data
#         data = json.loads(json_input)
#     except json.JSONDecodeError as e:
#         return f"Error parsing JSON: {e}"
#      # Extract NPC information
#     npcs = data.get('npcs', [])
#     if not npcs:
#         return "No NPCs found in the data."
    
#     npc = npcs[0]  # Assuming we're interested in the first NPC
#     npc_info = npc.get('info', {})
#     first_name = npc_info.get('firstName', 'Unknown')
#     last_name = npc_info.get('lastName', 'Unknown')
    
#     # Extract current action
#     cur_action = npc.get('Action', {})
#     action_name = cur_action.get('actionName', 'None')  # Default to 'None' if not present
#     action_oid = cur_action.get('param', {}).get('oid', 'None')  # Default to 'None' if not present

#     # NPC name mapping
#     npc_names = {
#         10006: "Satoshi",
#         10007: "Popcat",
#         10008: "Pepe",
#         10009: "Musk"
#     }
#     result = f''' '''
#     return result

def parse_isFindingPeopletoTalk(json_input):

    try:
        # Load the JSON data
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}" 
     # Extract NPC information
    npcs = data.get('npcs', [])
    if not npcs:
        return "No NPCs found in the data."
    
    npc = npcs[0]  # Assuming we're interested in the first NPC
    npc_info = npc.get('info', {})
    first_name = npc_info.get('firstName', 'Unknown')
    last_name = npc_info.get('lastName', 'Unknown')
    
    # Extract current action
    cur_action = npc.get('Action', {})
    action_name = cur_action.get('actionName', 'None')  # Default to 'None' if not present
    action_oid = cur_action.get('param', {}).get('oid', 'None')  # Default to 'None' if not present
    action_id = cur_action.get('actionId', '0')  # Default to 'None' if not present

    result = False
    if int(action_id) == 112:
        result = True
    return result





def parse_talking_from_java(json_input):
    try:
        # Load the JSON data
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"
    
    # world_time_ms = data.get('world', {}).get('time', 0)
    # try:
    #     world_time = datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
    # except (OSError, ValueError):
    #     world_time = "Invalid world time"

    npcs = data.get('npcs', [])
    if not npcs:
        return "No NPCs found in the data."
    
    npc = npcs[0]  # Assuming we're interested in the first NPC

     # NPC name mapping
    npc_names = {
        10006: "Satoshi",
        10007: "Popcat",
        10008: "Pepe",
        10009: "Musk"
    }
    
    # Extract talking information
    talk_info = npc.get('talk', {})
    is_talking = talk_info.get('isTalking', False)
    talk_contents = talk_info.get('contents', [])
    
    if is_talking and talk_contents:
        talk_summary = "\n".join([
            f"{npc_names.get(content.get('sender'), 'Unknown')} said to {npc_names.get(content.get('target'), 'Unknown')}: {content.get('content', 'None')} \n"
            for content in talk_contents
        ])
    else:
        talk_summary = "No ongoing conversation."
    output_text = (
        # f"Time now is: {world_time}, {talk_summary}"
        f"{talk_summary}"
    )
    
    return output_text, is_talking

def parse_isIdling(json_input):
    try:
        # Load the JSON data
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"
    # npcs = data.get('npcs', [])
    # npc = npcs[0]
    # idling = npc.get('status', {})
    idling = data['npcs'][0]['status']
    if idling == "free":
        print("I am free", idling)
        return True
    print('I am not free', idling)
    return False









def parse_npc_info_formemory(json_input):
    try:
        # Load the JSON data
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"
    
    # Extract world time and convert from milliseconds to a readable format
    world_time_ms = data.get('world', {}).get('time', 0)
    try:
        world_time = datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
    except (OSError, ValueError):
        world_time = "Invalid world time"

    # Extract NPC information
    npcs = data.get('npcs', [])
    if not npcs:
        return "No NPCs found in the data."
    
    npc = npcs[0]  # Assuming we're interested in the first NPC

    # NPC name mapping
    npc_names = {
        10006: "Satoshi",
        10007: "Popcat",
        10008: "Pepe",
        10009: "Musk"
    }
    
    
    # Extract talking information
    talk_info = npc.get('talk', {})
    is_talking = talk_info.get('isTalking', False)
    talk_contents = talk_info.get('contents', [])
    
    if is_talking and talk_contents:
        talk_summary = "\n".join([
            f"{npc_names.get(content.get('sender'), 'Unknown')} said to {npc_names.get(content.get('target'), 'Unknown')}: {content.get('content', 'None')} \n"
            for content in talk_contents
        ])
    else:
        talk_summary = "No ongoing conversation."

    # Compile the extracted information into a readable format
    output_text = (
        f"At {world_time}, {talk_summary}"
    )
    
    return output_text


def talkingInstruction(npcId, words):
    """
    Generate a JSON instruction for NPC to talk.
    
    Args:
    npcId (str): The ID of the NPC.
    words (str): The words the NPC will say.
    
    Returns:
    str: A formatted JSON string for the instruction.
    """
    if not isinstance(npcId, str) or not isinstance(words, str):
        raise ValueError("Both npcId and words must be strings.")
    
    words = words.replace('"', '\\"')  # Escape quotes in the text
    instruction = {
        "actionId": 110,
        "npcId": npcId,
        "data": {
            "content": words
        }
    }
    return json.dumps(instruction, indent=4)