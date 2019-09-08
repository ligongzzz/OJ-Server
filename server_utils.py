import socket


def send_msg(sock: socket.socket, msg_to_send: str):
    try:
        msg_to_send = str(len(msg_to_send)) + '~' + msg_to_send
        sock.send(msg_to_send.encode('utf-8'))
    except Exception as err:
        print(err)
        print('发送信息时发生错误')
