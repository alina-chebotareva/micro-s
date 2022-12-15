from threading import Thread
from getpass import *
import socket
import sys
import logging
import pickle
import time


class Client:
    def __init__(self, server_ip, port):
        self.server_ip = server_ip
        self.port = port
        self.connect()
        self.sync()

    def connect(self):
        sock = socket.socket()
        try:
            sock.connect((self.server_ip, self.port))
        except ConnectionRefusedError:
            print("Подключение к серверу не доступно")
            sys.exit(0)
        self.sock = sock
        print("Соединение с сервером установлено")


    def receive_data(self):
        while True:
            try:
                self.data = self.sock.recv(1024)
                if not self.data:
                    sys.exit(0)
                self.status = pickle.loads(self.data)[0]
                # Вывод сообщений от других пользователей
                if self.status == "message":
                    print(f"\n{pickle.loads(self.data)[2]}->", pickle.loads(self.data)[1])
                    logging.info(f"{self.sock.getsockname()} получил данные от сервера: {pickle.loads(self.data)[1]}")
                else:
                    self.data = pickle.loads(self.data)[1]
            except OSError:
                break

    def send_password(self):
        password = getpass(self.data)
        self.sock.send(pickle.dumps(["password", password]))
        time.sleep(0.25)

    def auth(self):
        self.username = input("Введите имя пользователя: ")
        self.sock.send(pickle.dumps(["auth", self.username]))
        time.sleep(0.25)

    def register(self):
        self.username = input("Введите новое имя пользователя: ")
        self.sock.send(pickle.dumps(["register", self.username]))
        time.sleep(0.25)

    def success(self):
        print(self.data)
        self.status = "ready"
        self.username = self.data.split(" ")[2]
        logging.info("Клиент авторизировался")



    def sync(self):
        Thread(target=self.receive_data).start()
        print("'exit' - разорвать соединение, 'shutdown' - выключить сервер")
        self.status = None
        while True:
            if self.status:
                if self.status == "auth":
                    self.auth()
                elif self.status == "register":
                    self.register()
                    logging.info(f"Пользователь зарегистрирован")
                elif self.status == "password":
                    self.send_password()
                elif self.status == "success":
                    self.success()
                else:
                    user_input = input(f"{self.username}> ")
                    if user_input != "":
                        if user_input == "exit":
                            print(f"Разрыв соединения {self.sock.getsockname()} с сервером по команде")
                            logging.info(f"Разрыв соединения {self.sock.getsockname()} с сервером по команде")
                            close_connection = pickle.dumps(["exit", "Разрыв соедиенения", self.username])
                            self.sock.send(close_connection)
                            self.sock.close()
                            sys.exit(0)
                        elif user_input == "shutdown":
                            shutdown_server = pickle.dumps(["shutdown", "Отключение сервера", self.username])
                            self.sock.send(shutdown_server)
                        send_message = pickle.dumps(["message", user_input, self.username])
                        self.sock.send(send_message)
                        logging.info(f"Отправка данных от {self.sock.getsockname()} на сервер: {user_input}")


def main():
    user_port = input("Введите порт сервера:")
    user_ip = input("Введите IP-адрес сервера:")
    Client(user_ip, int(user_port))


if __name__ == "__main__":
    main()




