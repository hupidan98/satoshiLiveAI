
import sys
sys.path.append('./DBmanipulation')
sys.path.append('../DBmanipulation')
sys.path.append('./SenidngReceiving')
sys.path.append('../SenidngReceiving')
import os

from DBCon import establish_sql_connection
import BehaviorJavaBufferDB
import BehaviorInstructionDB 
import CommentReplyJavaBufferDB

import socket
import struct
import header_pb2
import Message_pb2
import server_node_pb2
import configparser
import time
import json
import copy
import traceback
import datetime


import threading
import select



def build_packet_buffer(header_data, message_data):
    header_length = len(header_data)
    message_length = len(message_data)
    
    # 打印调试信息
    #print(f'Header length: {header_length}, Header data: {header_data}')
    #print(f'Message length: {message_length}, Message data: {message_data}')
    
    # 构建字节缓冲区，按顺序写入头部长度、头部数据、消息长度和消息数据
    byte_buffer = struct.pack('>I', header_length) + header_data + struct.pack('>I', message_length) + message_data
    
    # 打印调试信息
    #print(f'Packet data: {byte_buffer}')
    
    return byte_buffer


def wrap_packet_buffer(byte_buffer_data):
    length = len(byte_buffer_data)
    #total_length = length + 4
    
    # 打印调试信息
    #print(f'Byte buffer length: {length}')
    #print(f'Total length: {total_length}')
    
    # 构建新的字节缓冲区
    new_raw_data = struct.pack('>I', length) + byte_buffer_data
    
    # 打印调试信息
    #print(f'New raw data: {new_raw_data}')
    
    return new_raw_data


def make_header(command, config):
    header = header_pb2.Header()
    header.rtype = "!"
    header.command = command
    header.source = config['DEFAULT']['source']
    header.destination = "app.z1.s2.P1"
    header.code = 0
    header.dstScope = 0
    header.cmd = 0
    return header.SerializeToString()


def make_message(input_text):
    message = Message_pb2.Message()
    message.content = bytes(input_text, 'utf-8')
    return message.SerializeToString()


def ip_to_int(ip_address):
    packed_ip = socket.inet_aton(ip_address)
    return struct.unpack("!I", packed_ip)[0]


def make_node_message():
    node = server_node_pb2.server_node()
    #节点ID
    node.node_id = "app.z1.s2.A1"
    #Ip 地址，转成int类型  #ip_to_int(socket.gethostbyname(socket.gethostname()))
    node.ip_lan = 1111111
    #node.ip_public = 3232235777
    #端口
    node.port_lan= 2528
    #node.port_public= 2528
    #UDP 配置
    #node.domain= ""
    #node.udp_port= 0
    #固定值：连接通道方式
    node.channel = 0
    #节点类型：固定值，A代表python ai 服务
    node.type = "A"

    message = Message_pb2.Message()
    message.content = node.SerializeToString()
    return message.SerializeToString()

def parse_response(response, isiterative = True): 

    print(response)
    
    if isiterative:
        total_length = struct.unpack('>I', response[:4])[0]
        packet_data = response[4:4 + total_length]
    else:
        packet_data = response

     # 解析 Header 的长度
    header_length = struct.unpack('>I', packet_data[:4])[0]
    header_data = packet_data[4:4 + header_length]
    header = header_pb2.Header()
    header.ParseFromString(header_data)

    # 解析 Message 的长度
    message_length_start = 4 + header_length
    message_length = struct.unpack('>I', packet_data[message_length_start:message_length_start + 4])[0]
    message_data_start = message_length_start + 4
    message_data = packet_data[message_data_start:message_data_start + message_length]
    message = Message_pb2.Message()
    message.ParseFromString(message_data)

    return header, message

def receive_input(sock):
    response = sock.recv(4096)
    print(response)
    print('Received response(receiving):')

    header, message = parse_response(response, isiterative = True)
    print(f'Header: {header}')
    print(f'Message: {message.content.decode("utf-8")}')
    response_fron_java = message.content.decode("utf-8")
    return response_fron_java


def receive_input_long(sock):
    length_bytes = sock.recv(4)
    data_length = int.from_bytes(length_bytes, 'big')
    print(data_length)
    # response = sock.recv(data_length)
    total_data_length = data_length
    received_data = b""
    counter = 0
    while len(received_data) < total_data_length:
        # print(min(4096, total_data_length - len(received_data)))
        data = sock.recv(min(4096, total_data_length - len(received_data)))
        # print(data)
        if not data:
            # 如果没有接收到数据，表示对方关闭了连接
            print("Connection closed by peer before sending all data.")
            break
        received_data += data

        # print(counter)
        counter += 1
    # print("Received all data:", received_data.decode())
    response = received_data


    print('Received response long:')

    header, message = parse_response(response,isiterative = False)
    print(f'Header: {header}')
    print(f'Message: {message.content.decode("utf-8")}')
    output = message.content.decode("utf-8")
    return output






def execute_instruction(sock, config, instruction, head_num):

    #npc行为同步数据
    header_data = make_header(head_num, config)
    message_data = make_message(instruction)
    packet_data = build_packet_buffer(header_data, message_data)
    wrapped_packet_data = wrap_packet_buffer(packet_data)

    sock.sendall(wrapped_packet_data)
    return 0

    # Establish Connection
def createsocket(ip_txt, port_int):
    config = configparser.ConfigParser()
    config.read('config.properties')

    #向java服务注册节点数据
    node_header_data = make_header(-1, config)
    node_message_data = make_node_message()
    packet_node_data = build_packet_buffer(node_header_data, node_message_data)
    wrapped_packet_node_data = wrap_packet_buffer(packet_node_data)

    #第一步：创建与java服务的连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip_txt, port_int)
    # server_address = ('aitown.infinitytest.cc', 2521)
    print(f'Connecting to {server_address[0]} port {server_address[1]}')
    sock.connect(server_address)

    #第二步: 注册当前服务器节点信息：发送节点注册消息
    sock.sendall(wrapped_packet_node_data)
    inital_back = receive_input(sock)
    print(inital_back)
    return sock, config

def is_socket_connected(sock):
    if not sock:
        return False
    try:
        # Use getsockopt to check for socket errors
        error_code = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        return error_code == 0  # If error_code is 0, the socket is connected
    except socket.error as e:
        print(f'Socket error: {e}')
        return False

def reconnect_socket(ip_txt, port_int, max_retries=5):
    attempt = 0
    # while attempt < max_retries:
    while True:
        try:
            # Create and connect the socket
            sock, config = createsocket(ip_txt, port_int)

            # Check if the socket is connected
            if is_socket_connected(sock):
                print("Socket is connected.")
                return sock, config
            else:
                print("Socket not connected. Reconnecting...")
        except Exception as e:
            print(f"Error connecting socket: {e}")
        
        # Wait before attempting to reconnect
        time.sleep(5)  # Wait 5 seconds before retrying
        attempt += 1
        print(f"Reconnection attempt {attempt} of {max_retries} failed.")

    # If all attempts fail, raise an exception or handle it as needed
    print("Max reconnection attempts reached. Unable to connect.")
    return None, None



def split_response_npcs(input_from_java):
    data = json.loads(input_from_java)

    # Initialize the list to hold the NPC dictionaries
    npc_dict = {}

    # Extract the world and mapObj
    world = data["data"]["world"]
    
    # Convert the Unix timestamp to a human-readable string
    world_time_ms = world.get("time")
    if world_time_ms:
        world["time"] = datetime.datetime.fromtimestamp(world_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')

    map_obj = data["data"]["mapObj"]

    # Iterate over each NPC and create a dictionary with npcId as key and the required data as value
    for npc in data["data"]["npcs"]:
        npc_id = npc["npcId"]
        npc_data = {
            "npcId": npc_id,
            "world": copy.deepcopy(world),
            "mapObj": copy.deepcopy(map_obj),
            "npc": copy.deepcopy(npc)
        }
        npc_dict[str(npc_id)] = npc_data

    return npc_dict

def receive_data(sock):
    while True:
        try:
            print("Waiting to receive data...")
            input_from_java = receive_input_long(sock)
            print("Received input from Java:", input_from_java)

            # Parse input
            data = json.loads(input_from_java)
            print("Parsed input successfully:", data)

            if data['command'] == 10101:
                # npc behavior
                try:
                    npcInputSingle = data['data']
                    print(npcInputSingle)
                    print(npcInputSingle.keys())
                    
                    dt_object = datetime.datetime.fromtimestamp(npcInputSingle['world']['time'] / 1000.0)
                    time_stamp = dt_object.strftime('%Y-%m-%d %H:%M:%S')  # Format to MySQL datetime format
                    npcId = npcInputSingle['npcs'][0]['npcId']


                    content = json.dumps(npcInputSingle)  # Convert the content to JSON format
                    db_connection = establish_sql_connection()

                    # Insert into table using formatted datetime string
                    BehaviorJavaBufferDB.insert_into_table(db_connection, time_stamp, int(npcId), content)
                    
                except Exception as e:
                    print(f"Failed to insert data for npcId {npcId}: {e}")
                    traceback.print_exc()
                else:
                    print(f"Data for npcId {npcId} inserted successfully.")
            # elif data['command'] == 10101:
            #     # npc Accouncement
            #     try:
            #         # do something
            #         print(data)
            #     except Exception as e:
            #         print(f"Failed to insert data for npcId {npcId}: {e}")
            #         traceback.print_exc()
            #     else:
            #         print(f"Data for npcId {npcId} inserted successfully.")
            elif data['command'] == 10103:
                # npc reply to comment from player
                try:
                    # do something
                    playerCommentData = data['data']
                    npcId = playerCommentData['npcId']
                    requestId = data['requestId']
                    senderId = playerCommentData['ChatData']['sender']
                    msgId = playerCommentData['ChatData']['msgId']
                    content = playerCommentData['ChatData']['content']
                    dt_object = datetime.datetime.fromtimestamp(playerCommentData['ChatData']['time'] / 1000.0)
                    time_stamp = dt_object.strftime('%Y-%m-%d %H:%M:%S') 
                    CommentReplyJavaBufferDB.insert_into_table(db_connection, time_stamp, npcId, msgId, senderId, content)
                except Exception as e:
                    print(f"Failed to insert data for npcId {npcId}: {e}")
                    traceback.print_exc()
                else:
                    print(f"Data for npcId {npcId} inserted successfully.")
        except Exception as e:
            print(f"Error in receive_data: {e}")
            traceback.print_exc()
 


def send_data(sock, config):
    while True:
        print("Checking for unprocessed instructions...")
        try:
            db_conn = establish_sql_connection()
            instruction_from_db = BehaviorInstructionDB.get_earliest_unprocessed_instruction(db_conn)
            print(f"Instruction from DB: {instruction_from_db}")
            if instruction_from_db is not None:
                curTime, npcId, instruction_str = instruction_from_db[0], instruction_from_db[1], instruction_from_db[2]
                head_num = 10100  # Set the appropriate head_num or pull dynamically if needed
                print('Sending instruction:', instruction_str)
                # Execute the instruction and mark it as processed
                execute_instruction(sock, config, instruction_str, head_num)
                BehaviorInstructionDB.mark_instruction_as_processed(db_conn, curTime, npcId)
                print(f"Sent instruction: {instruction_str} for npcId {npcId} and marked as processed.")
            else:
                print("No unprocessed instructions found.")
                time.sleep(5)  # Sleep for 5 seconds before checking again
        except Exception as e:
            print(f"Error in send_data: {e}")
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    # ip_java = 'aitown.infinitytest.cc'
    # ip_java = 'satoshi-ai.live'
    # port_java = 2521
    print("Current working directory:", os.getcwd())
    
    config = configparser.ConfigParser()
    # Adjust path to look for config.ini in AImodule regardless of the current directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config.ini')
    config.read(config_path)
    
    print("Config sections found:", config.sections())
    
    if 'NetworkSocket' not in config:
        print("Error: 'NetworkSocket' section not found in config.ini")
    ip_java = config['NetworkSocket']['ip_java']
    port_java = int(config['NetworkSocket']['port_java'])

    # Create socket and set to blocking mode (default m
    # ode)
    socket_receive, config_receive = reconnect_socket(ip_java, port_java)
    
    # Initial command to execute before starting threads
    init_command = '''
    {"command": 10102, "data": {}}
    '''
    header_number = 10102

    # Execute the initial instruction with the init_command and header_number 10102
    print("Executing initial command before starting threads...")
    execute_instruction(socket_receive, config_receive, init_command, header_number)

    # Start the receiving and sending threads
    receive_thread = threading.Thread(target=receive_data, args=(socket_receive,))
    send_thread = threading.Thread(target=send_data, args=(socket_receive, config_receive))

    # Set threads as daemons so they exit when the main program exits
    receive_thread.daemon = True
    send_thread.daemon = True

    # Start both threads
    print('Starting receiving data...')
    receive_thread.start()
    print('Starting sending data...')
    send_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)  # Keep main thread alive to allow threads to run
    except KeyboardInterrupt:
        print("Interrupted, closing socket.")
        socket_receive.close()
      
