import sys
import os

import pandas as pd
import numpy as np
import json
import re
import pickle

# Add the base directory (one level up from AnnCtrl)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)


from DBConnect import DBCon 
from DBConnect import CmtRpyDBJavaBuffer
from DBConnect import CmtRpyDBInstruction
  
from DBConnect import AnnDBAnnBuffer

from DBConnect import BhrDBMemStre
from DBConnect import BhrDBReflection





import CmtRpyLgcGPTProcess
# import CmtRpyManualProcess
# import CmtRpyInstToMemStre
# import CmtRpyInputToMemStre



def choiceOneToReply():
    db_conn = DBCon.establish_sql_connection()
    input_from_java = CmtRpyDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)
    print(input_from_java)

    if input_from_java is None:
        print('Nothing to process so far')
        print()
        print()
        return 0
    
    npcId = input_from_java[2]
    requestId = input_from_java[0]
    time = input_from_java[1]
    msgId = input_from_java[3]
    senderId = input_from_java[4]
    content = input_from_java[5]

    # Get all comments for that npc
    all_comments = CmtRpyDBJavaBuffer.get_unprocessed_entries_of_npc(db_conn, npcId)
    print(all_comments)
    # Prepare data for DataFrame
    data = []
    requestIdtoMark = []
    for comment in all_comments:
        requestId, time, npcId, msgId, senderId, content, isProcessed = comment
        requestIdtoMark.append(requestId)
        embedding = CmtRpyLgcGPTProcess.get_embedding(content)
        # Deserialize the embedding back to a list
        data.append([requestId, time, npcId, msgId, senderId, content, embedding])

    # Define DataFrame columns
    columns = ['requestId', 'time', 'npcId', 'msgId', 'senderId', 'content', 'embedding']

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)


    # Get memeory strem later
    
    # Get reflect later

    # Get daily schedule later

    # Get announcement
    ann_contents = AnnDBAnnBuffer.get_latest_n_announcements(db_conn, npcId, 50)
    
    ann_contents_str = str(ann_contents)

    
    # Select one randomly
    comment_row_reply = df.sample(n=1)
    commet_to_reply = comment_row_reply['content']

    #Creating Reply
    reply = CmtRpyLgcGPTProcess.replyToComment(ann_contents_str,  commet_to_reply)

    # Sent Reply
    instruction_to_give = json.dumps({
        "actionId": 117,
        "npcId": npcId,
        "data": {
            "content": reply,
            "chatData": {
                "msgId": msgId,
                "sname": str(senderId),  # Assuming `sname` can use `senderId` as a string
                "sender": senderId,
                "type": 0,  # Assuming a static value for type; change if needed
                "content": reply,
                "time": int(time.timestamp() * 1000),  # Convert datetime to milliseconds
                "barrage": 0  # Assuming a static value for barrage; change if needed
            }
        }
    }, ensure_ascii=False)

    
    print(instruction_to_give)
    CmtRpyDBInstruction.insert_into_instruction_table(db_conn, requestId, time, npcId, msgId, instruction_to_give, isProcessed=False)
    

    for rid in requestIdtoMark:
        CmtRpyDBJavaBuffer.mark_entry_as_processed(db_conn, rid )
    # Example instruction.
    # {
    # "actionId": 117,
    # "npcId": 10002,
    # "data": {
    #     "playerId": "123132131",
    #     "content": "123132131",
    #     "msgId": "123132131",
    # }
    # }
    
    #Mark as Processed.


    return 0 
