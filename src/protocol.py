"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self, command):
        self.command = command
    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, command, channel):   # {"command": "join", "channel": "#cd"}
        super().__init__(command)
        self.channel = channel

    def __str__(self):
        return f'{{"command": "{self.command}", "channel": "{self.channel}"}}'
       


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, command, user):    # {"command": "register", "user": "student"}
        super().__init__(command)
        self.user = user

    def __str__(self):
        return f'{{"command": "{self.command}", "user": "{self.user}"}}'
        

    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, command, message, ts, channel = None):   # {"command": "message", "message": "Hello World", "channel":"cd", "ts": 1615852800}
        super().__init__(command)
        self.message = message
        self.channel = channel
        self.ts = ts

    def __str__(self):
        if self.channel != None:
            return f'{{"command": "{self.command}", "message": "{self.message}", "channel": "{self.channel}", "ts": {self.ts}}}'
        else: return f'{{"command": "{self.command}", "message": "{self.message}", "ts": {self.ts}}}'


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        user = RegisterMessage("register", username)
        return user

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        channel2join = JoinMessage("join", channel)
        return channel2join

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        timestamp = datetime.now().timestamp()
        msg = TextMessage("message", message, int(timestamp), channel)
        return msg

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        if type(msg) == RegisterMessage:
            msgjson = reg_json(msg)
        elif type(msg) == JoinMessage:
            msgjson = join_json(msg)
        elif type(msg) == TextMessage:
            msgjson = text_json(msg)

        msg_length = len(msgjson).to_bytes(2, "big")
        connection.send(msg_length + msgjson)
        

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        header = connection.recv(2) 
        header = int.from_bytes(header, "big")
        body = connection.recv(header).decode("utf-8")

        if header != 0:
            try:
                data = json.loads(body)
                com = data["command"]
                if com == "register":
                    return RegisterMessage("register", data["user"])
                elif com == "join":
                    return JoinMessage("join", data["channel"])
                elif com == "message":
                    if "channel" in data:
                        return TextMessage("message", data["message"], data["ts"], data["channel"])
                    else:
                        return TextMessage("message", data["message"], data["ts"])
            except:
                raise CDProtoBadFormat(body)


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
    
# functions to handle different types of msg    

def reg_json(msg):
    msg = json.dumps({"command": "register", "user": msg.user})
    return msg.encode("utf-8")

def join_json(msg):
    msg = json.dumps({"command": "join", "channel": msg.channel})
    return msg.encode("utf-8")

def text_json(msg):
    if msg.channel == None:  
        msg = json.dumps({"command": "message", "message": msg.message.strip(), "ts": msg.ts})
    else:
        msg = json.dumps({"command": "message", "message": msg.message.strip(), "channel": msg.channel, "ts": msg.ts})
    return msg.encode("utf-8")
