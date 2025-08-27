import socket
import threading
from datetime import datetime


def receber_mensagem_servidor(sock):        #Deixa o client "ouvindo" a conexão com o servidor aguardando qualquer informação (confirmações, erros ou resultados do sorteio) seja exibida ao usuário

    while True:
        try:
            info = sock.recv(1024).decode('utf-8')      #Deixa o client ouvindo, define tamanho da mensagem e decodifica.
            if not info:        #Deixa o client ouvindo, define tamanho da mensagem e decodifica.
                print("Conexão com o servidor foi perdida")
                break
            print(f"\n[SERVIDOR] Aguardando suas configurações ou aposta: {info}")      #Recebe configurações p/ cada client


        except (socket.error, ConnectionResetError):         #Encerra conexão
            print("Conexão com o servidor foi perdida.")
            break 


def mandar_mensagem_servidor(sock):     #Escuta o usuário e garante que o que ele digitar seja enviado para o servidor de forma contínua, enquanto a conexão estiver ativa.

    while True:
        try:
            print("\nEsperando sua aposta, após digita-lá aperte ENTER")
            mensagem = input("")
            sock.send(mensagem.encode('utf-8'))     #Codifica a mensagem e envia para o servidor

        except (socket.error, ConnectionResetError):    #Trata perda de conexão com o client
            break 


def main():     #Configura a conexão, inicia as duas threads essenciais para a comunicação (uma para ouvir e outra para falar) e garante que o programa encerre de forma segura.

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #Cria o socket "ouvinte" do client#Instancia o objeto ouvinte do cliente
    server_address = ('localhost', 12345)

    try:
        client_socket.connect(server_address)   #Garante que a conexão com o servidor só será feita na porta correta

        thread_receber = threading.Thread(target=receber_mensagem_servidor, args=(client_socket,))      #Cria a Thread "ouvinte" do cliente
        thread_receber.start()

        thread_enviar = threading.Thread(target=mandar_mensagem_servidor, args=(client_socket,))         #Cria a Thread mensageira do cliente
        thread_enviar.start()

        thread_enviar.join()        #Deixa as duas threads rodarem de forma paralela, enquanto o client estiver ativo

    except ConnectionRefusedError:      #Trata o erro de enderessamento da conexão
        print(f"Não foi possível conectar ao servidor em {server_address}. Certifique-se de que o servidor está em execução.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        client_socket.close()       #Libera a conexão com o servidor

if __name__ == '__main__':
    main()    




