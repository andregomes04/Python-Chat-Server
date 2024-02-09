import fcntl
import logging
import os
import sys
import socket
import selectors

from src.protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.channel = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # criar selector e registar stdin no selector 
        self.sel = selectors.DefaultSelector() #(selector diz se input veio do teclado ou do servidor, util na parte do loop)
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.send) 
        self.sel.register(self.sock, selectors.EVENT_READ, self.rcv) 
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK) 
        print("Client started")

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        try:
            self.sock.connect(('localhost', 1234))
            self.sock.setblocking(False)
        except Exception as e:
            logging.error(f"Error connecting to server: {str(e)}")
            sys.exit(1)


    def send(self):
            input = sys.stdin.read()
            if input == "exit\n":
                print("{} left the chat.".format(self.name))
                sys.exit()
            elif input.startswith("/join"):
                self.channel = input.split()[1]
                msg = CDProto.join(self.channel)
            else:
                msg = CDProto.message(input, self.channel)

            try:
                CDProto.send_msg(self.sock, msg)
            except Exception as e:
                logging.error(f"Error sending message: {str(e)}")


    def rcv(self):
        try:
            msg = CDProto.recv_msg(self.sock)
            if msg != None:
                print(msg.message)
                logging.debug(msg.message)
        except CDProtoBadFormat as e:
            logging.error(f"Error parsing message: {str(e)}")
        except Exception as e:
            logging.error(f"Error receiving message: {str(e)}")

    def loop(self):
        """Loop indefinetely."""
        msg_reg = CDProto.register(self.name)

        try:
            CDProto.send_msg(self.sock, msg_reg)
        except Exception as e:
            logging.error(f"Error registering user: {str(e)}")
            sys.exit(1)
            
        try:
            while True:
                events = self.sel.select()
                for key, mask in events:
                    callback = key.data
                    callback()

        except KeyboardInterrupt as e:
            self.sel.unregister(sys.stdin)
            self.sel.unregister(self.sock)
            self.sock.close()