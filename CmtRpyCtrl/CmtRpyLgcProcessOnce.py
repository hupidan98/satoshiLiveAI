import sys
import os

import DBConnect.DBCon as DBCon 
from DBConnect import CommentReplyDBJavaBuffer
from DBConnect import CommentReplyDBInstruction
from DBConnect import BehaviorDBMemStre
from DBConnect import BehaviorDBReflection
from DBConnect import BehaviorScheduleDB


import CmtRpyLgcGPTProcess
# import CommentReplyManualProcess
# import CommentReplyInstToMemStre
# import CommentReplyInputToMemStre



import pandas as pd
import numpy as np
import json
import re
import pickle


def choiceOneToReply():
    db_conn = DBCon.establish_sql_connection()
    input_from_java = CommentReplyDBJavaBuffer.get_earliest_unprocessed_entry(db_conn)
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
    all_comments = CommentReplyDBJavaBuffer.get_unprocessed_entries_of_npc(db_conn, npcId)
    print(all_comments)
    # Prepare data for DataFrame
    data = []
    for comment in all_comments:
        requestId, time, npcId, msgId, senderId, content, isProcessed = comment
        embedding = CmtRpyLgcGPTProcess.get_embedding(content)
        # Deserialize the embedding back to a list
        data.append([requestId, time, npcId, msgId, senderId, content, embedding])

    # Define DataFrame columns
    columns = ['requestId', 'time', 'npcId', 'msgId', 'senderId', 'content', 'embedding']

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)

    # Get memeory strem
    
    # Get reflect
    # Get daily schedule
    # Get announcement
    
    # Process, find the closest match

    #Creating Reply

    # Sent Reply
    instruction_to_give = json.dumps({
        "actionId": 117,
        "npcId": npcId,
        "data": {
            "content": content,
            "chatData": {
                "msgId": msgId,
                "sname": str(senderId),  # Assuming `sname` can use `senderId` as a string
                "sender": senderId,
                "type": 0,  # Assuming a static value for type; change if needed
                "content": content,
                "time": int(time.timestamp() * 1000),  # Convert datetime to milliseconds
                "barrage": 0  # Assuming a static value for barrage; change if needed
            }
        }
    }, ensure_ascii=False)

    
    print(instruction_to_give)
    CommentReplyDBInstruction.insert_into_instruction_table(db_conn, requestId, time, npcId, msgId, instruction_to_give, isProcessed=False)
    
    CommentReplyDBJavaBuffer.mark_entry_as_processed(db_conn, requestId)
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
