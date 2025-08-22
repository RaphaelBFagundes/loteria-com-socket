import socket
import threading
from datetime import datetime


def receber_mensagem_servidor(sock):

    while True:
        try:
            info = sock.recv(1024).decode('utf-8')
            if not info:
                print("Conexão com o servidor foi perdida")
                break
            print(f"\n[SERVIDOR] Aguardando suas configurações ou aposta: {info}")


        except (socket.error, ConnectionResetError):
            print("Conexão com o servidor foi perdida.")
            break 


def mandar_mensagem_servidor(sock):

    while True:
        try:
            print("\nEsperando sua aposta, após digita-lá aperte ENTER")
            mensagem = input("")
            sock.send(mensagem.encode('utf-8'))

        except (socket.error, ConnectionResetError):
            break 


def main():

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 12345)

    try:
        client_socket.connect(server_address)

        thread_receber = threading.Thread(target=receber_mensagem_servidor, args=(client_socket,))
        thread_receber.start()

        thread_enviar = threading.Thread(target=mandar_mensagem_servidor, args=(client_socket,))
        thread_enviar.start()

        thread_enviar.join()

    except ConnectionRefusedError:
        print(f"Não foi possível conectar ao servidor em {server_address}. Certifique-se de que o servidor está em execução.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        client_socket.close()

if __name__ == '__main__':
    main()    




