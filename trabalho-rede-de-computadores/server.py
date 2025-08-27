from datetime import datetime
from random import sample
from collections import deque
import time
import socket
import threading

lock = threading.Lock()         #Define um lock para garantir que as threads sejam executadas de forma segura

apostas_pendentes = deque()         #Cria fila de apostas

configuracoes = {}

def gerenciar_mensagens(id, addr):      #Essa função  lida com todas as interações do cliente, validando as entradas, aplicando a lógica de negócio e respondendo de forma apropriada cada usuário.

    print(f"[{addr}] Cliente conectado.")   #Identifica o client para o servidor

    agora = datetime.now()
    mensagem_de_conexao=agora.strftime("%H:%M:%S") + ": CONECTADO!!"
    id.send(mensagem_de_conexao.encode('utf-8'))        #Envia mensagem de conexão ao client de cada id printando Hora:Minuto:segundos de forma individual

    while True:
        try:
            info = id.recv(1024).decode('utf-8')    #Deixa o servidor ouvindo e decodifica.
            if not info:
                print(f"[{addr}] Cliente desconectou.")
                break

            info = info.strip() #Separa a string enviada pelo cliente em partes, com base em espaços em branco
            partes = info.split()

            with lock:  #Separa a string enviada pelo cliente em partes, com base em espaços em branco
                if addr not in configuracoes:   #Define default de configurações 
                    configuracoes[addr] = {
                        "inicio": 0,
                        "fim": 100,
                        "qtd": 5
                    }

                if partes[0].startswith(":"):   #Entende o simbolo ':' como um comando e atribui os valores com base nas partes definidas no comando split
                    try:
                        comando_ini = int(partes[1])
                        comando_fim = int(partes[3])
                        comando_qtd = int(partes[5])

                        if comando_qtd > (comando_fim - comando_ini + 1):       #Trata erro de números digitados
                            resposta = "ERRO: Vocês precisa apostar em uma quantidade de números que não exceda o range do sorteio. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue

                        configuracoes[addr]["inicio"] = comando_ini
                        configuracoes[addr]["fim"] = comando_fim
                        configuracoes[addr]["qtd"] = comando_qtd

                        print(f"[{addr}] Configurações atualizadas para o usuário: {configuracoes[addr]}")
                        resposta = "Configurações atualizadas com sucesso!"
                        id.send(resposta.encode('utf-8'))           #Atualiza a aposta do usuário e envia codificada

                    except (ValueError, IndexError):        #Trata erro de formatos
                        resposta = "ERRO: O formato do comando está errado. Use ':inicio num :fim num :qtd num'"
                        id.send(resposta.encode('utf-8'))

                else:
                    try:
                        aposta = list(map(int, partes))         #Transformaa a string de numeros em valores inteiros
                        qtd_esperada = configuracoes[addr]['qtd']        #Pega a quantidade de numeros escolhida pelo usuário


                        if len(aposta) != qtd_esperada:     #Trata o erro de quantidade de numeros != de quantidade escolhida
                            resposta = f"ERRO: Vocês precisa apostar {qtd_esperada} números. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue

                        if len(aposta) != len(set(aposta)):        #Trata o erro de numeros repetidos
                            resposta = "ERRO: Você não pode apostar no mesmo número mais de uma vez. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue        #Verifica se todos os números apostados estão dentro do range definido pelo cliente.

                            #teste no simbolo de comparação para n entre as config de inicio e fim
                        if not all(configuracoes[addr]['inicio'] < n < configuracoes[addr]['fim'] for n in aposta):
                            resposta = f"ERRO: Vocês precisa apostar um número entre {configuracoes[addr]['inicio']} e {configuracoes[addr]['fim']}. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue        

                        aposta_info = {      #Cria uma estrutura com as informacoes da aposta
                            "addr": addr,
                            "numeros": aposta
                        }
                        apostas_pendentes.append(aposta_info)   #Manda a aposta para a fila
                        print(f"[{addr}] Aposta registrada: {aposta}")
                        resposta =f"Aposta de {len(aposta)} números registrada com sucesso. Boa sorte!"
                        id.send(resposta.encode('utf-8'))

                    except (ValueError, IndexError):    #Trata erro de formatos
                        resposta = "ERRO: O formato do comando está errado. Use números separados por espaço."
                        id.send(resposta.encode('utf-8'))   

        except (socket.error, ConnectionResetError):
            print(f"[{addr}] Conexão com o cliente foi perdida.")
            break
    
def agenda_sorteio():           #Gerencia e agenda o sorteio a cada 60 segundos
    while True:
        print("\n[LOTERIA] Iniciando contagem de 60 segundos para o próximo sorteio...")
        time.sleep(60)           #Deixa o sistema esperando o tempo definido
        print("[LOTERIA] Tempo esgotado! Realizando sorteio...")

        with lock:      #Garante que as threads sejam executadas de forma segura
            apostas_para_sorteio = list(apostas_pendentes)       #Cria uma copia da fila
            apostas_pendentes.clear()        #Limpa a fila

        if not apostas_para_sorteio:        #Trata o caso de nenhuma aposta ter sido feita
            print("[LOTERIA] Nenhuma aposta foi feita neste ciclo. O sorteio foi cancelado.")
            continue

        config_sorteio = configuracoes.get(apostas_para_sorteio[0]["addr"], {
           "inicio": 0,
           "fim": 100,
           "qtd": 5
        })
    
        try:
            numeros_disponiveis = range(config_sorteio["inicio"], config_sorteio["fim"] + 1)        #Define o range permitido
            numeros_escolhidos = sample(numeros_disponiveis, config_sorteio["qtd"])         #Define os numeros dentro do range

            print(f"[LOTERIA] Números sorteados: {sorted(numeros_escolhidos)}")            #Sorteia os numeros

            for aposta_info in apostas_para_sorteio:
                id_cliente = get_client_connection_from_addr(aposta_info["addr"])       #A função get_client_connection_from_addr identifica o cliente pelo endereço addr
                if not id_cliente:
                    continue

                aposta = aposta_info["numeros"]
                acertos = set(aposta) & set(numeros_escolhidos)     #Verifica os acertos utilizando o conceito de conjunto

                resultado_msg = f"\n--- RESULTADO DO SORTEIO ---\nNumeros Sorteados: {sorted(numeros_escolhidos)}\nSua aposta{sorted(aposta)}"

                if acertos: #Verifica se houve algum acerto
                    resultado_msg += f"\nParabens! Voce acertou {len(acertos)} numero(s): {sorted(list(acertos))}."
                else:
                    resultado_msg += "\nQue pena! Voce nao acertou nenhum numero."
                    
                id_cliente.send(resultado_msg.encode('utf-8'))      #Envia o resultado para o cliente

        except ValueError as e:     #Trata erro de formato
            print(f"[LOTERIA] ERRO ao realizar sorteio: {e}. Verifique as configuracoes e refaça sua aposta.")
            
def get_client_connection_from_addr(addr):      #Busca a conexão de um cliente específico a partir de seu endereço de rede
   
    for thread in threading.enumerate():        #Percorre a lista de threads abertas (O conjunto de threads abertas para cada cliente possui seu addr como nome)
        if thread.name == str(addr):
            return thread._args[0]      #Se houver uma thread com o addr desejado, retorna o id da conexão
    return None     #Se nenhuma thread for encontrada, retorna None

def main():
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       #Cria o socket "ouvinte" do servidor
    server_address = ('localhost', 12345)       #Define a porta do servidor
    server_socket.bind(server_address)      #Associa a porta ao socket
    server_socket.listen(5)             #Define o limite de conexões pendentes
    print(f"[SERVIDOR] Servidor escutando em {server_address}...")
    
    loteria_thread = threading.Thread(target=agenda_sorteio, name="agenda_sorteio")     #Cria uma Thread para a agenda dos sorteios    
    loteria_thread.daemon = True        #Garante que a thread seja encerrada ao encerrar o programa
    loteria_thread.start()          #Inicia a trhread de agenda disparando o sitema e o cronômetro
    
    while True:
        id, addr = server_socket.accept()       #Aguarda a conexão de um novo cliente passando id e addr
        cliente_thread = threading.Thread(target=gerenciar_mensagens, args=(id, addr), name=str(addr))      #Cria uma Thread para cada cliente conectado ao servidor
        cliente_thread.start()          #Inicia a Thread do cliente

if __name__ == '__main__':
    main()

    
