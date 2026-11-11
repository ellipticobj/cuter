import socket
import sys
import threading
import curses
from curses import wrapper
from datetime import datetime

class Client:
    def __init__(self, stdscr, debug=False):
        '''
        :3
        '''
        curses.use_default_colors()
        self.stdscr = stdscr
        self.debug = debug
        self.running = True
        self.host = "localhost" if debug else "luna.hackclub.app"
        self.port = 7171
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = ""
        self.setupui()

    def setupui(self):
        '''
        initializes the windows for the chat and input for persistant prompts
        '''
        curses.curs_set(1)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)

        self.rows, self.cols = self.stdscr.getmaxyx()

        self.inputwin = curses.newwin(1, self.cols, self.rows-1, 0)
        self.chatwin = curses.newwin(self.rows-1, self.cols, 0, 0)
        self.chatwin.scrollok(True)

    def exitscreen(self, message):
        rows, cols = self.stdscr.getmaxyx()
        width = min(60, cols-4)
        height = 6

        win = curses.newwin(height, width, max(0, rows//2-2), max(0, (cols-width)==2))

        try:
            messages = message.split('\n')[:2]
            for i, line in enumerate(messages):
                trunc = line[:width-2]
                win.addstr(i, 0, trunc.center(width))

            prompt = "[RETURN to exit] "
            win.addstr(height-1, (width-len(prompt))//2, prompt)
            win.refresh()

            while True:
                key = self.stdscr.getch()
                if key == curses.KEY_ENTER or key in [10, 13]:
                    break
        except curses.error:
            pass
        finally:
            win.erase()
            self.stdscr.refresh()

    def display(self, message):
        '''
        prints a message
        '''
        try:
            timestamp = datetime.now().strftime("%H:%M")
            self.chatwin.addstr(f"[{timestamp}] {message}\n")
            self.chatwin.refresh()
            self.inputwin.refresh()
        except:
            pass

    def getusrname(self):
        '''
        sets user username
        '''
        self.stdscr.clear()
        self.stdscr.refresh()

        prompt = "> "
        scrtext = f"enter username (leave empty for anon)\n{prompt}"
        usrnamewin = curses.newwin(3, 50, 5, 5)

        usrnamewin.addstr(0, 0, scrtext)
        usrnamewin.refresh()

        curses.echo()
        username = usrnamewin.getstr(scrtext.count('\n'), len(prompt), 20).decode()
        curses.noecho()

        usrnamewin.erase()
        self.stdscr.touchwin()
        self.stdscr.refresh()

        self.username = username.strip() if username.strip() else "anon"
        self.display(f"joined with username: {self.username}")

    def usecustomserverprompt(self):
        '''
        asks user if they want to connect to the default server
        '''
        self.stdscr.clear()
        self.stdscr.refresh()

        prompt = "(Y/n)> "
        scrtext = f"do you want to connect to the default server?\nip: {self.host}\nport: {self.port}\n{prompt}"
        win = curses.newwin(6, 50, 5, 5)

        win.addstr(0, 0, scrtext)
        win.refresh()

        curses.echo()
        match win.getstr(scrtext.count('\n'), len(prompt), 20).decode().strip().lower():
            case "n":
                usedef = False

            case _:
                usedef = True
        curses.noecho()
        win.erase()

        self.stdscr.touchwin()
        self.stdscr.refresh()

        return usedef

    def getcustomserver(self):
        '''
        gets user's server config
        '''
        self.stdscr.clear()
        self.stdscr.refresh()

        prompt = "> "
        hostscrtext = f"host {prompt}"
        portscrtext = f"port {prompt}"
        self.port = None
        self.host = None
        win = curses.newwin(6, 50, 5, 5)

        while not self.host:
            win.addstr(0, 0, hostscrtext)
            win.refresh()
            curses.echo()
            self.host = win.getstr(hostscrtext.count('\n'), len(prompt+hostscrtext), 20).decode().strip().lower()
            curses.noecho()
            win.erase()

        while not self.port:
            win.addstr(0, 0, f"host >   {self.host}")
            win.addstr(1, 0, portscrtext)
            win.refresh()
            curses.echo()
            self.port = win.getstr(portscrtext.count('\n')+1, len(prompt+portscrtext), 20).decode().strip().lower()
            curses.noecho()
            win.erase()

            if len(str(self.port)) != 4:
                self.port = None
                win.addstr(3, 0, "port needs to be 4 digits")
                continue

            try:
                self.port = int(self.port)
                if not (1 <= self.port <=65535):
                    raise ValueError
            except:
                self.port = None
                win.addstr(3, 0, "port needs to be an integer between 1 and 65535")
                continue

        win.addstr(0, 0, f"host >   {self.host}")
        win.addstr(1, 0, f"port >   {self.port}")
        win.addstr(3, 0, "[RETURN to continue]")
        win.refresh()

        while True:
            key = self.stdscr.getch()
            if key == curses.KEY_ENTER or key in [10, 13]:
                break

        win.erase()
        self.stdscr.touchwin()
        self.stdscr.refresh()

    def connect(self):
        '''
        attempts to connect to server with username
        '''
        usedefault = self.usecustomserverprompt()

        if not usedefault:
            self.getcustomserver()

        if not self.host or not self.port:
            self.exitscreen("critical error:\nhost or port does not exist")

        print(f"  HOST: {self.host}")
        print(f"  PORT: {self.port}")

        self.getusrname()

        self.display("connecting...")

        try:
        # attempts to connect to server
        # timeout set to 5 seconds
            self.client.settimeout(10)
            self.client.connect((self.host, int(self.port)))
            self.client.send(self.username.encode())

            response = self.client.recv(1024).decode()
            if response.lower() == "connection rejected":
                self.exitscreen("connection rejected by server")
                self.running = False
                return False
            self.display(response)

            self.client.settimeout(None)
            return True
        except ConnectionRefusedError:
            self.exitscreen("connection refused\nserver may be offline")
            self.running = False
        except socket.timeout:
            self.exitscreen("connection timed out\nserver not responding")
            self.running = False
        except Exception as e:
            self.exitscreen(f"connection failed\nerror: {str(e)}\nreport this to https://github.com/ellipticobj/cli-messenger/issues/new")
            self.running = False
        finally:
            if self.running == False:
                return False

    def receiveloop(self):
        '''
        receive messages from server
        '''
        while self.running:
            try:
                message = self.client.recv(1024).decode()
                if not message:
                    raise ConnectionError("server disconnection")

                self.display(message)
            except Exception as e:
                self.display(f"error occured in receiveloop: {e}\n exiting...")
                self.running = False
                break

    def inputloop(self, prompt = "> "):
        '''
        receive user input (messages)
        '''
        buf = ''

        while self.running:
            try:
                self.inputwin.clear()
                self.inputwin.addstr(0, 0, prompt + buf)
                self.inputwin.refresh()

                key = self.inputwin.getch()

                if key == curses.KEY_ENTER or key in [10, 13]:
                    if buf.strip():
                        try:
                            self.client.settimeout(5)
                            self.client.send(buf.encode())
                            buf = ''
                        except socket.timeout:
                            self.display("server not responding... disconnecting...")
                            self.running = False
                            break
                        finally:
                            self.client.settimeout(None)

                elif key == curses.KEY_BACKSPACE or key == 127:
                    buf = buf[:-1]
                elif 0 <= key < 256:
                    buf += chr(key)

            except Exception as e:
                self.display(f"error occured in inputloop: {e}")
                self.running = False

    def run(self):
        '''
        runs the app (duh)
        '''
        if not self.connect():
            return

        receivethread = threading.Thread(target=self.receiveloop, daemon=True)
        receivethread.start()

        self.inputloop()
        self.client.close()
        curses.endwin()

def main(stdscr):
    args = sys.argv[1:]
    debug = False
    if args:
        if (args[0] in ["-d", "--debug"]):
            debug = True

    client = Client(stdscr, debug=debug)
    client.run()

    while client.running:
        try:
            curses.napms(500) # instead of time.sleep because sigma
        except Exception as e:
            return e
    return "disconnected"

if __name__ == "__main__":
    error = ""
    try:
        error = wrapper(main)
    except KeyboardInterrupt:
        pass # TODO
    except curses.error:
        pass

    print(error)
    print("program quit")
