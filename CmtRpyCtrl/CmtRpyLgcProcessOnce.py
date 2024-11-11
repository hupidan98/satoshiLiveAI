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
        requestId_fromdb, time_fromdb, npcId_fromdb, msgId_fromdb, senderId_fromdb, content_fromdb, isProcessed_fromdb, sname_fromdb = comment
        requestIdtoMark.append(requestId_fromdb)
        embedding = CmtRpyLgcGPTProcess.get_embedding(content_fromdb)
        # Deserialize the embedding back to a list
        data.append([requestId_fromdb, time_fromdb, npcId_fromdb, msgId_fromdb, senderId_fromdb, content_fromdb, embedding, sname_fromdb])

    # Define DataFrame columns
    columns = ['requestId', 'time', 'npcId', 'msgId', 'senderId', 'content', 'embedding', 'sname']

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
    reply_tosent = CmtRpyLgcGPTProcess.replyToComment(ann_contents_str,  commet_to_reply)

    # Sent Reply
    requestId_tosent = str(comment_row_reply['requestId'].iloc[0])
    npcId_tosent = str(comment_row_reply['npcId'].iloc[0])
    msgId_tosent = str(comment_row_reply['msgId'].iloc[0])
    senderId_tosent = str(comment_row_reply['senderId'].iloc[0])
    time_tosent = comment_row_reply['time'].iloc[0]  # Get the first value if `time` is a Series
    sname_tosent = str(comment_row_reply['sname'].iloc[0])


    instruction_to_give = json.dumps({
        "actionId": 117,
        "npcId": str(npcId),
        "data": {
            "content": str(reply_tosent),
            "chatData": {
                "msgId": str(msgId_tosent),
                "sname": str(sname_tosent),  # Assuming `sname` can use `senderId` as a string
                "sender": str(senderId_tosent),
                "type": 0,  # Assuming a static value for type; change if needed
                "content": str(reply_tosent),
                "time": str(int(time_tosent.timestamp() * 1000)),  # Convert datetime to milliseconds
                "barrage": 0  # Assuming a static value for barrage; change if needed
            }
        }
    }, ensure_ascii=False)

    
    print(instruction_to_give)
    CmtRpyDBInstruction.insert_into_instruction_table(db_conn, requestId_tosent, time_tosent, npcId_tosent, msgId_tosent, instruction_to_give, isProcessed=False)
    

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
