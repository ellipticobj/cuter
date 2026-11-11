import socket
import threading
from datetime import datetime
import sys
import time

class Server:
    def __init__(self, host='0.0.0.0', port=7171):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.clients = {} # dictionary of socket: username
        self.running = True
        self.lock = threading.Lock()

        self.whitelist = {} # set of whitelisted ips
        self.blacklist = {} # set of blacklisted ips

        self.whitelistenabled = False # enables/disables whitelist (ONLY allows list of allowed users)
        self.blacklistenabled = False # enables/disables blacklist (allows everyone EXCEPT disallowed users)

        self.profanityfilter = 'off' # off, block, censor
        self.profanitywords = set([]) # add blocked words here

        self.setup()

    def setup(self):
        '''sets up the server'''
        if self.whitelistenabled and self.blacklistenabled:
            print("both whitelist and blacklist cannot be enabled at the same time")
            sys.exit()

        self.server.bind((self.host, self.port))
        self.server.listen()
        self.log(f"server listening at {self.host}:{self.port}")

    def log(self, message, end='\n'):
        '''prints a log + stores it in a log file'''
        logfile = "server.log"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entr = f"[{now}] {message}"
        print(entr, end=end)
        with open(logfile, "a") as file:
            file.write(f"{entr}\n")

    def acceptclient(self):
        while self.running:
            try:
                client, addr = self.server.accept()
                clientthread = threading.Thread(
                    target=self.handleclient,
                    args=(client,addr),
                    daemon=True
                )
                clientthread.start()
            except OSError:
                break
            except Exception as e:
                self.log(f"error at clientthread: {e}")

    def handleclient(self, clsock, claddr):
        '''handles client connection'''
        username = clsock.recv(1024).decode()
        clip, clport = claddr

        if self.validate(clip):
            with self.lock:
                self.clients[clsock] = username
                self.broadcast(f"{username} joined")
                self.log(f"{username} joined from {clip}:{claddr}")
        else:
            clsock.send("connection rejected".encode())
            clsock.close()
            return

        try:
            while self.running:
                message = clsock.recv(1024).decode()
                if not message:
                    break
                self.procmessage(username, message)
        except Exception as e:
            self.log(f"error handling client {username}: {e}")

        with self.lock:
            if clsock in self.clients:
                del self.clients[clsock]
                self.broadcast(f"{username} has left the chat!")
                self.log(f"{username} disconnected")
            clsock.close()

    def procmessage(self, username, message):
        '''handles messages'''
        if message.startswith('/'):
            pass

        if self.profanityfilter:
            message = self.filter(message)

        if message:
            self.broadcast(f"{username}: {message}")
            self.log(f"{username}: {message}")

    def filter(self, message):
        words = message.split()
        for i, word in enumerate(words):
            if word.lower() in self.profanitywords:
                if self.profanityfilter == "block":
                    return None
                elif self.profanityfilter == "censor":
                    words[i] = "*" * len(word)
        return " ".join(words)

    def validate(self, addr):
        '''
        checks if client's ip is black/whitelisted
        returns true if user is allowed to connect, falso if disallowed
        '''
        if self.whitelistenabled:
            if addr in self.whitelist:
                return True
            else:
                return False
        if self.blacklistenabled:
            if addr in self.blacklist:
                return False
            else:
                return True
        return True

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message.encode())
            except:
                del self.clients[client]
                self.broadcast(f"{self.clients[client]} has left the chat!")
                self.log(f"{self.clients[client]} disconnected")
                client.close()

    def shutdown(self):
        '''shutting down server'''
        self.running = False
        self.log("shutting down server...")

        with self.lock:
            for client in self.clients:
                try:
                    client.send("server is shutting down".encode())
                    client.close()
                except:
                    pass
            self.clients.clear()

        try:
            self.server.close()
        except:
            pass

    def run(self):
        self.log("starting threads...")
        try:
            acceptthread = threading.Thread(
                target = self.acceptclient,
                daemon=True
            )
            acceptthread.start()
        except Exception as e:
            self.log(f"error: {e}")
        self.log("done")

def main():
    server = None
    try:
        print("starting server...")
        server = Server()
        server.run()

        server.log("checking if server is alive")
        while server.running:
            server.log("server is alive")
            try:
                time.sleep(20)
                server.log("checking if server is alive")
            except KeyboardInterrupt:
                server.shutdown()
                break
    except Exception as e:
        print(f"server error: {e}")


if __name__ == "__main__":
    main()
