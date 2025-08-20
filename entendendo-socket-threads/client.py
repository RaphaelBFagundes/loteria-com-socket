import socket
import threading
from datetime import datetime

# --- Funções do Cliente ---
def receive_messages(sock):
    """
    Thread 2 do Cliente: Recebe e imprime mensagens do servidor.
    """
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("Conexão com o servidor foi fechada.")
                break
            print(f"\n[SERVIDOR]: {data}")
            
        except (socket.error, ConnectionResetError):
            print("Conexão com o servidor foi perdida.")
            break

def send_messages(sock):
    """
    Thread 1 do Cliente: Lê a entrada do usuário e envia para o servidor.
    """
    while True:
        try:
            message = input("")
            sock.send(message.encode('utf-8'))
            
        except (socket.error, ConnectionResetError):
            break

def main():
    """
    Função principal do Cliente.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 12345)

    try:
        client_socket.connect(server_address)
        
        # Inicia a thread para receber mensagens do servidor
        thread_receber = threading.Thread(target=receive_messages, args=(client_socket,))
        thread_receber.start()

        # Inicia a thread para enviar mensagens ao servidor
        thread_enviar = threading.Thread(target=send_messages, args=(client_socket,))
        thread_enviar.start()

        # Mantém a thread principal viva
        thread_enviar.join()
        
    except ConnectionRefusedError:
        print(f"Não foi possível conectar ao servidor em {server_address}. Certifique-se de que o servidor está em execução.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        client_socket.close()

if __name__ == '__main__':
    main()