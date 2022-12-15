from threading import Thread
import socket
import json
import pickle
import logging
import hashlib

class Server:
    def __init__(self, port):
        self.database = "./users.json"
        self.port = port
        self.users = []
        self.connections = []
        self.init_server()

    def registration(self, addr, conn, username):
        conn.send(pickle.dumps(["password", "Введите новый пароль: "]))
        password1 = self.generate_hash(pickle.loads(conn.recv(1024))[1])
        conn.send(pickle.dumps(["success", f"Успешная регистрация, {username}"]))
        self.users.append({username: {'password': password1, 'address': addr[0]}})
        self.database_write()
        self.users = self.database_read()


    def broadcast(self, msg, conn, username):
        for connection in self.connections:
            if connection != conn:
                connection.send(pickle.dumps(["message", msg, username]))

    def client_logic(self, conn, address):
        self.authorization(address, conn)
        while True:
            data = conn.recv(1024)

            if data:
                status, data, username = pickle.loads(data)
                if status == "message":
                    self.broadcast(data, conn, username)
                elif status == "shutdown":
                    for connection in self.connections:
                        connection.send(pickle.dumps(["message", f"{username} выключил сервер", "~SERVER~"]))
                        connection.close()
                    self.sock.close()
                    break
                elif status == "exit":
                    conn.close()
                    self.connections.remove(conn)
                    for connection in self.connections:
                        connection.send(pickle.dumps(["message", f"{username} отключился от сервера", "~SERVER~"]))
                    break
            else:
                # Закрываем соединение
                conn.close()
                self.connections.remove(conn)
                logging.info(f"Отключение клиента {address}")
                break

    def authorization(self, addr, conn):
        conn.send(pickle.dumps(["auth", "Введите имя пользователя: "]))
        username = pickle.loads(conn.recv(1024))[1]
        self.users = self.database_read()

        is_registered = False
        for user in self.users:
            for key, value in user.items():
                if key == username:
                    is_registered = True
                    password1 = value['password']
                    conn.send(pickle.dumps(["password", "Введите свой пароль: "]))
                    password = pickle.loads(conn.recv(1024))[1]
                    conn.send(pickle.dumps(["success", f"Добро пожаловать, {username}"]))

        if not is_registered:
            self.registration(addr, conn, username)

    def database_read(self):
        with open(self.database, 'r') as f:
            users = json.load(f)
        return users

    def database_write(self):
        with open(self.database, 'w') as f:
            json.dump(self.users, f, indent=4)



    def generate_hash(self, password):
        # Генерация хеша для безопасного хранение паролей
        key = hashlib.md5(password.encode() + b'salt').hexdigest()
        return key

    def init_server(self):
        sock = socket.socket()
        sock.bind(('', self.port))
        sock.listen(5)
        self.sock = sock
        while True:
            conn, addr = self.sock.accept()
            Thread(target=self.client_logic, args=(conn, addr)).start()
            self.connections.append(conn)

def main():
    port = 9564
    Server(port)


if __name__ == "__main__":
    main()

