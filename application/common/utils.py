"""Утилиты"""
import sys
import json
import os

sys.path.append("../")

import application.common.variables as vrb
from application.common.deco import log_it

# sys.path.append("../")

# base_dir = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(os.path.join(base_dir, "common"))

@log_it
def get_message(client):
    '''
    Утилита приёма и декодирования сообщения
    принимает байты выдаёт словарь, если принято что-то другое отдаёт ошибку значения
    :param client:
    :return:
    '''

    encoded_response = client.recv(vrb.MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(vrb.ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@log_it
def send_message(sock, message):
    '''
    Утилита кодирования и отправки сообщения
    принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:
    '''

    js_message = json.dumps(message)
    encoded_message = js_message.encode(vrb.ENCODING)
    sock.send(encoded_message)
