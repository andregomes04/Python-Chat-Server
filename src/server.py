"""CD Chat server program."""
import logging
import selectors
import socket
from src.protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""

    def __init__(self):
        self.sel = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', 1234))
        self.sock.listen(100)
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        self.sockdata = {}
        print("server started")

    def accept(self, sock, mask):
        conn, addr = sock.accept() 
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        try:
            msg = CDProto.recv_msg(conn)
        except CDProtoBadFormat:
            msg = None

        if msg != None:
            self.handle_message(conn, msg)
        else:
            self.handle_disconnect(conn)

    def handle_message(self, conn, msg):
        if msg.command == "register":
            self.reg_user(conn, msg.user)
        elif msg.command == "join":
            self.join(conn, msg.channel)
        elif msg.command == "message":
            self.send(conn, msg)

    def reg_user(self, conn, user):
        self.sockdata[conn] = [user]
        print("{} connected.".format(self.sockdata[conn][0]))
        logging.debug("{} connected.".format(self.sockdata[conn][0]))

    def join(self, conn, channel):
        values = self.sockdata.get(conn)
        values.append(channel)
        self.sockdata[conn] = values
        print("{} joined {}".format(self.sockdata[conn][0], channel))
        logging.debug("{} joined {}".format(self.sockdata[conn][0], channel))

    def send(self, sender_conn, msg):
        for conn, values in self.sockdata.items():
            if msg.channel == None or msg.channel in values:
                sender_username = self.sockdata[sender_conn][0]
                recipient_username = values[0]
                CDProto.send_msg(conn, msg)
                print(" {} is sending a message to {} in #{}.".format(recipient_username, sender_username, msg.channel))
                logging.debug(" {} is sending a message to {} in #{}.".format(recipient_username, sender_username, msg.channel))
       
    def handle_disconnect(self, conn):
        print("{} disconnected".format(self.sockdata[conn][0]))
        logging.debug("{} disconnected.".format(self.sockdata[conn][0]))
        self.sockdata.pop(conn)
        self.sel.unregister(conn)
        conn.close()
        

    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

