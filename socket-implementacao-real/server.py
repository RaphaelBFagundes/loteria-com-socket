from datetime import datetime
from random import sample
from collections import deque
import time
import socket
import threading

lock = threading.Lock()

apostas_pendentes = deque()

configuracoes = {}

def gerenciar_mensagens(id, addr):

    print(f"[{addr}] Cliente conectado.")

    agora = datetime.now()
    mensagem_de_conexao=agora.strftime("%H:%M:%S") + ": CONECTADO!!"
    id.send(mensagem_de_conexao.encode('utf-8'))

    while True:
        try:
            info = id.recv(1024).decode('utf-8')
            if not info:
                print(f"[{addr}] Cliente desconectou.")
                break

            info = info.strip()
            partes = info.split()

            with lock:
                if addr not in configuracoes:
                    configuracoes[addr] = {
                        "inicio": 0,
                        "fim": 100,
                        "qtd": 5
                    }

                if partes[0].startswith(":"):
                    try:
                        comando_ini = int(partes[1])
                        comando_fim = int(partes[3])
                        comando_qtd = int(partes[5])

                        if comando_qtd > (comando_fim - comando_ini + 1):
                            resposta = "ERRO: Vocês precisa apostar em uma quantidade de números que não exceda o range do sorteio. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue

                        configuracoes[addr]["inicio"] = comando_ini
                        configuracoes[addr]["fim"] = comando_fim
                        configuracoes[addr]["qtd"] = comando_qtd

                        print(f"[{addr}] Configurações atualizadas para o usuário: {configuracoes[addr]}")
                        resposta = "Configurações atualizadas com sucesso!"
                        id.send(resposta.encode('utf-8'))

                    except (ValueError, IndexError):
                        resposta = "ERRO: O formato do comando está errado. Use ':inicio num :fim num :qtd num'"
                        id.send(resposta.encode('utf-8'))

                else:
                    try:
                        aposta = list(map(int, partes))
                        qtd_esperada = configuracoes[addr]['qtd']

                        if len(aposta) != qtd_esperada:
                            resposta = f"ERRO: Vocês precisa apostar {qtd_esperada} números. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue

                        if len(aposta) != len(set(aposta)):
                            resposta = "ERRO: Você não pode apostar no mesmo número mais de uma vez. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue


                            #teste no simbolo de comparação para n entre as config de inicio e fim
                        if not all(configuracoes[addr]['inicio'] < n < configuracoes[addr]['fim'] for n in aposta):
                            resposta = f"ERRO: Vocês precisa apostar um número entre {configuracoes[addr]['inicio']} e {configuracoes[addr]['fim']}. Tente novamente."
                            id.send(resposta.encode('utf-8'))
                            continue

                        aposta_info = {
                            "addr": addr,
                            "numeros": aposta
                        }
                        apostas_pendentes.append(aposta_info)
                        print(f"[{addr}] Aposta registrada: {aposta}")
                        resposta =f"Aposta de {len(aposta)} números registrada com sucesso. Boa sorte!"
                        id.send(resposta.encode('utf-8'))

                    except (ValueError, IndexError):
                        resposta = "ERRO: O formato do comando está errado. Use números separados por espaço."
                        id.send(resposta.encode('utf-8'))   

        except (socket.error, ConnectionResetError):
            print(f"[{addr}] Conexão com o cliente foi perdida.")
            break
    
def agenda_sorteio():
    while True:
        print("\n[LOTERIA] Iniciando contagem de 60 segundos para o próximo sorteio...")
        time.sleep(60)
        print("[LOTERIA] Tempo esgotado! Realizando sorteio...")

        with lock:
            apostas_para_sorteio = list(apostas_pendentes)
            apostas_pendentes.clear()

        if not apostas_para_sorteio:
            print("[LOTERIA] Nenhuma aposta foi feita neste ciclo. O sorteio foi cancelado.")
            continue

        config_sorteio = configuracoes.get(apostas_para_sorteio[0]["addr"], {
           "inicio": 0,
           "fim": 100,
           "qtd": 5
        })
    
        try:
            numeros_disponiveis = range(config_sorteio["inicio"], config_sorteio["fim"] + 1)
            numeros_escolhidos = sample(numeros_disponiveis, config_sorteio["qtd"])

            print(f"[LOTERIA] Números sorteados: {sorted(numeros_escolhidos)}")

            for aposta_info in apostas_para_sorteio:
                id_cliente = get_client_connection_from_addr(aposta_info["addr"])
                if not id_cliente:
                    continue

                aposta = aposta_info["numeros"]
                acertos = set(aposta) & set(numeros_escolhidos)

                resultado_msg = f"\n--- RESULTADO DO SORTEIO ---\nNumeros Sorteados: {sorted(numeros_escolhidos)}\nSua aposta{sorted(aposta)}"

                if acertos:
                    resultado_msg += f"\nParabens! Voce acertou {len(acertos)} numero(s): {sorted(list(acertos))}."
                else:
                    resultado_msg += "\nQue pena! Voce nao acertou nenhum numero."
                    
                id_cliente.send(resultado_msg.encode('utf-8'))

#Revisar essa parte
        except ValueError as e:
            print(f"[LOTERIA] ERRO ao realizar sorteio: {e}. Verifique as configuracoes.")
            
def get_client_connection_from_addr(addr):
   
    for thread in threading.enumerate():
        if thread.name == str(addr):
            return thread._args[0]
    return None

def main():
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 12345)
    server_socket.bind(server_address)
    server_socket.listen(5)
    print(f"[SERVIDOR] Servidor escutando em {server_address}...")
    
    loteria_thread = threading.Thread(target=agenda_sorteio, name="agenda_sorteio")
    loteria_thread.daemon = True
    loteria_thread.start()
    
    while True:
        id, addr = server_socket.accept()
        # Inicia uma thread para lidar com o cliente que se conectou
        cliente_thread = threading.Thread(target=gerenciar_mensagens, args=(id, addr), name=str(addr))
        cliente_thread.start()

if __name__ == '__main__':
    main()
#Até aqui
    
