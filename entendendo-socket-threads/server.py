import socket
import threading
import time
from random import sample
from datetime import datetime

# --- Variáveis de Sincronização e Estado ---
lock = threading.Lock()
# Lista para armazenar as apostas recebidas de todos os clientes
apostas_pendentes = [] 
# Dicionário para armazenar as configurações da loteria por cliente
configuracoes = {} 

# --- Funções do Servidor ---
def handle_client_messages(conn, addr):
    """
    Thread 1 do Servidor: Recebe dados do cliente e processa comandos ou apostas.
    """
    print(f"[{addr}] Cliente conectado.")
    
    # Envia a mensagem de conexão imediata
    agora = datetime.now()
    mensagem_conexao = agora.strftime("%H:%M:%S") + ": CONECTADO!!"
    conn.send(mensagem_conexao.encode('utf-8'))
    
    while True:
        try:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                print(f"[{addr}] Cliente desconectou.")
                break
            
            # --- Processamento dos dados ---
            data = data.strip()
            partes = data.split()
            
            with lock:
                # Se o cliente não tem uma configuração padrão, cria uma
                if addr not in configuracoes:
                    configuracoes[addr] = {
                        "inicio": 0,
                        "fim": 100,
                        "qtd": 5
                    }

                if partes[0].startswith(':'):
                    # Processa comandos de configuração
                    try:
                        cmd_inicio = int(partes[1])
                        cmd_fim = int(partes[3])
                        cmd_qtd = int(partes[5])
                        
                        # Validação de range
                        if cmd_qtd > (cmd_fim - cmd_inicio + 1):
                            resposta = "ERRO: Quantidade de numeros excede o range do sorteio. Tente novamente."
                            conn.send(resposta.encode('utf-8'))
                            continue
                        
                        # Atualiza as configurações do cliente
                        configuracoes[addr]['inicio'] = cmd_inicio
                        configuracoes[addr]['fim'] = cmd_fim
                        configuracoes[addr]['qtd'] = cmd_qtd
                        
                        print(f"[{addr}] Configurações atualizadas para: {configuracoes[addr]}")
                        conn.send("Configurações atualizadas com sucesso.".encode('utf-8'))
                        
                    except (ValueError, IndexError):
                        conn.send("ERRO: Formato de comando invalido. Use ':inicio <num> :fim <num> :qtd <num>'".encode('utf-8'))
                
                else:
                    # Processa a aposta do cliente
                    try:
                        aposta = list(map(int, partes))
                        qtd_esperada = configuracoes[addr]['qtd']
                        
                        # Validação de quantidade
                        if len(aposta) != qtd_esperada:
                            conn.send(f"ERRO: Aposta deve ter {qtd_esperada} numeros.".encode('utf-8'))
                            continue

                        # Validação de duplicidade
                        if len(aposta) != len(set(aposta)):
                            conn.send("ERRO: Aposta nao pode ter numeros duplicados.".encode('utf-8'))
                            continue

                        # Validação de range da aposta
                        if not all(configuracoes[addr]['inicio'] <= n <= configuracoes[addr]['fim'] for n in aposta):
                            conn.send("ERRO: Numeros da aposta fora do range configurado.".encode('utf-8'))
                            continue

                        # Armazena a aposta com o endereço do cliente
                        aposta_info = {
                            "addr": addr,
                            "numeros": aposta
                        }
                        apostas_pendentes.append(aposta_info)
                        print(f"[{addr}] Aposta registrada: {aposta}")
                        conn.send(f"Aposta de {len(aposta)} numeros registrada. Boa sorte!".encode('utf-8'))
                    
                    except (ValueError, IndexError):
                        conn.send("ERRO: Formato de aposta invalido. Use numeros separados por espaco.".encode('utf-8'))
                        
        except (socket.error, ConnectionResetError):
            print(f"[{addr}] Conexão perdida.")
            break
            
def loteria_scheduler():
    """
    Thread 2 do Servidor: Executa o sorteio a cada 60 segundos.
    """
    while True:
        print("\n[LOTERIA] Iniciando contagem de 60 segundos para o próximo sorteio...")
        time.sleep(60)
        print("[LOTERIA] Tempo esgotado! Realizando sorteio...")

        # Armazena as apostas atuais antes de limpar a lista
        with lock:
            apostas_para_sorteio = list(apostas_pendentes)
            apostas_pendentes.clear()

        if not apostas_para_sorteio:
            print("[LOTERIA] Nenhuma aposta foi feita neste ciclo. O sorteio foi cancelado.")
            continue
        
        # O sorteio deve seguir a configuração da última aposta válida recebida
        # A lógica mais simples é usar a configuração de um dos clientes que apostou
        # Neste caso, pegaremos o primeiro da lista, mas uma implementação mais robusta
        # poderia usar um sistema de "loterias múltiplas"
        
        # Encontra a configuração mais recente entre os clientes
        config_sorteio = configuracoes.get(apostas_para_sorteio[0]["addr"], {
            "inicio": 0, "fim": 100, "qtd": 5
        })
        
        try:
            numeros_disponiveis = range(config_sorteio["inicio"], config_sorteio["fim"] + 1)
            numeros_sorteados = sample(numeros_disponiveis, config_sorteio["qtd"])
            
            print(f"[LOTERIA] Numeros sorteados: {sorted(numeros_sorteados)}")
            
            # Compara as apostas com os números sorteados
            for aposta_info in apostas_para_sorteio:
                conn_cliente = get_client_connection_from_addr(aposta_info["addr"])
                if not conn_cliente:
                    continue
                
                aposta = aposta_info["numeros"]
                acertos = set(aposta) & set(numeros_sorteados)
                
                resultado_msg = f"\n--- RESULTADO DO SORTEIO ---\nNumeros sorteados: {sorted(numeros_sorteados)}\nSua aposta: {sorted(aposta)}"
                
                if acertos:
                    resultado_msg += f"\nParabens! Voce acertou {len(acertos)} numero(s): {sorted(list(acertos))}."
                else:
                    resultado_msg += "\nQue pena! Voce nao acertou nenhum numero."
                    
                conn_cliente.send(resultado_msg.encode('utf-8'))
                
        except ValueError as e:
            print(f"[LOTERIA] ERRO ao realizar sorteio: {e}. Verifique as configuracoes.")
            
def get_client_connection_from_addr(addr):
    """
    Função auxiliar para encontrar a conexão de um cliente.
    """
    for thread in threading.enumerate():
        if thread.name == str(addr):
            return thread._args[0]
    return None

def main():
    """
    Função principal do Servidor.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 12345)
    server_socket.bind(server_address)
    server_socket.listen(5)
    print(f"[SERVIDOR] Servidor escutando em {server_address}...")
    
    # Inicia a thread que fará o sorteio a cada 60 segundos
    loteria_thread = threading.Thread(target=loteria_scheduler, name="loteria_thread")
    loteria_thread.daemon = True
    loteria_thread.start()
    
    while True:
        conn, addr = server_socket.accept()
        # Inicia uma thread para lidar com o cliente que se conectou
        cliente_thread = threading.Thread(target=handle_client_messages, args=(conn, addr), name=str(addr))
        cliente_thread.start()

if __name__ == '__main__':
    main()