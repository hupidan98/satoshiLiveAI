import json
from datetime import datetime

def parse_npc_info(json_input):
    # Load the JSON data
    data = json.loads(json_input)
    
    # Extract world time and convert from milliseconds to a readable format
    world_time_ms = data['world']['time']
    world_time = datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract map objects
    map_objects = data['mapObj']
    map_details = "\n".join([f"Object Name: {obj['objName']}, Location: ({obj['X']}, {obj['Y']}), Status: {obj['status']}" 
                             for obj in map_objects])
    
    # Extract NPC information
    npc = data['npcs'][0]
    npc_info = npc['info']
    first_name = npc_info['firstName']
    last_name = npc_info['lastName']
    # learned = npc_info['learned']
    # lifestyle = npc_info['lifestyle']
    # living_area = npc_info['living_area']

    # Extract current action
    cur_action = npc['curAction']
    action_name = cur_action.get('actionName', None)  # Get 'actionName' or None if not present
    action_oid = cur_action.get('param', {}).get('oid', None)  # Get 'oid' inside 'param', or None if not present

    
    # Extract talking information
    talk_info = npc.get('talk', {})
    is_talking = talk_info.get('isTalking', False)
    talking_to = talk_info.get('talkingTo', [])
    talk_contents = talk_info.get('contents', [])
    
    talk_summary = "No ongoing conversation."
    if is_talking and talk_contents:
        talk_summary = "\n".join([
            f"Sender: {content['sender']}, Target: {content['target']}, Time: {datetime.fromtimestamp(content['time'] / 1000.0).strftime('%Y-%m-%d %H:%M:%S')}, Content: {content['content']}"
            for content in talk_contents
        ])
    
    # Compile the extracted information into a readable format
    output_text = (
        f"Time: {world_time}\n\n"
        f"NPC Information:\n"
        f"  First Name: {first_name}\n"
        f"  Last Name: {last_name}\n"
        f"Map Objects:\n{map_details}\n\n"
        f"NPC Current Action:\n"
        f"  Action Name: {action_name}\n"
        f"  Target Object ID: {action_oid}\n\n"
        f"Talking Information:\n{talk_summary}"
    )
    
    return output_text

def talkingInstruction(npcId, words):
    toReturn = f'''
    {{
        "actionId": 110,
        "npcId": "{npcId}",
        "data": {{
            "content": "{words}"
        }}
    }}
    '''
    return toReturn