#Notificar o usuário que conectou exibindo o horário de conexão e uma mensagem (FEITO)
#O usuário deve passar os parametros do range de números a serem sorteados (FEITO)
#O usuário deve passar quantos números ele deseja apostar (FEITO)
#O usuário deve passar os números em que deseja apostar separados por espaço (FEITO)
#Caso o usuário não defina o range do sorteio, será definido por padrão de 0 a 100 com 5 números sorteados (FEITO)

#OBS: Tratamento de erro - Não pode possuir números repitidos nas aposta


#O usuário pode definir a qualquer momento o range da próxima aposta utilizando :X :Y :Z para o range e qtd de números
#O usuário pode definir a qualquer momento o tamanho da próxima aposta utilizando X Y para os números de desejo
#Thread 1 cliente - O usuário pode criar novas apostas durante o jogo
#Thread 2 cliente - O usuário estará aguardando os numeros sorteados pelo sistema, quando os receber deve imprimir na tela e voltar a aguardar novos valores 
#Thread 1 servidor - O servidor armazenará os valores digitados em uma lista e voltar a aguardar novas apostas
#Thread 2 servidor - Será iniciada aguardando por 1 minuto, e fazendo sorteio dos números conforme configurado
#pelo usuário. Ao terminar o sorteio, ela verificará se o usuário fez apostas (percorrendo a lista referenciada acima), e
#verificando se alguma aposta foi sorteada. Após isso, ela enviará o resultado do sorteio ao cliente, e informará quais
#números ele acertou. A lista será então zerada e um novo ciclo será iniciado.

from random import sample
from datetime import datetime

# Notifica o usuário com a hora de conexão
agora = datetime.now()
hora_conexao = agora.strftime("%H:%M:%S")
print(f"Olá! Conectado às {hora_conexao}. Bem-vindo ao sistema de sorteio!")
print()
print("-=" * 50)
print()

while True:
    # Obtém o range de números ou define o padrão
    try:
        inicio_range_input = input("Digite o range inicial do sorteio (ou pressione Enter para usar 0): ")
        inicio_range = int(inicio_range_input) if inicio_range_input else 0

        fim_range_input = input("Digite o range final do sorteio (ou pressione Enter para usar 100): ")
        fim_range = int(fim_range_input) if fim_range_input else 100

        # Obtém a quantidade de números a serem sorteados ou define o padrão
        qtd_numeros_input = input("Quantos números deseja sortear? (ou pressione Enter para usar 5): ")
        qtd_numeros = int(qtd_numeros_input) if qtd_numeros_input else 5

        # Adição da nova condição: a quantidade de números a apostar não pode exceder o range
        tamanho_range = fim_range - inicio_range + 1
        if qtd_numeros > tamanho_range:
            print(f"\nERRO: Você precisa apostar em uma quantidade de números que não exceda o range do sorteio ({tamanho_range} números).")
            print("Por favor, defina os valores novamente.")
            print()
            print("-=" * 50)
            print()
            continue # Volta ao início do loop para redefinir os valores
            
        print(f"\nRange de sorteio definido de {inicio_range} a {fim_range}.")
        print(f"Você apostará em {qtd_numeros} números.")
        print()
        print("-=" * 50)
        print()
        
        break # Sai do loop se tudo estiver válido
        
    except ValueError:
        print("Entrada inválida. Por favor, digite apenas números inteiros.")
        print()
        print("-=" * 50)
        print()
        
# Obtém os números da aposta do usuário
while True:
    try:
        aposta_usuario_str = input(f"Digite os {qtd_numeros} números da sua aposta, separados por espaço: ")
        aposta_usuario = list(map(int, aposta_usuario_str.split()))

        # Verifica se a quantidade de números apostados é a correta
        if len(aposta_usuario) != qtd_numeros:
            print(f"Atenção: Você deve digitar exatamente {qtd_numeros} números. Tente novamente.")
            continue

        # Verifica se os números da aposta estão dentro do range definido
        numeros_invalidos = [num for num in aposta_usuario if not inicio_range <= num <= fim_range]
        if numeros_invalidos:
            print(f"Atenção: Os números {numeros_invalidos} estão fora do range de {inicio_range} a {fim_range}. Tente novamente.")
            continue
        
        break  # Sai do loop se a entrada for válida
    except ValueError:
        print("Entrada inválida. Digite apenas números inteiros separados por espaço.")
    
# Realiza o sorteio
numeros_disponiveis = range(inicio_range, fim_range + 1)
numeros_sorteados = sample(numeros_disponiveis, qtd_numeros)

print("\n-=-=-= RESULTADO DO SORTEIO =-=-=-")
print(f"Seus números apostados: {sorted(aposta_usuario)}")
print(f"Números sorteados: {sorted(numeros_sorteados)}")

# Compara os números e mostra o resultado
numeros_acertados = set(aposta_usuario) & set(numeros_sorteados)
quantidade_acertos = len(numeros_acertados)

if quantidade_acertos > 0:
    print(f"\nParabéns! Você acertou {quantidade_acertos} número(s): {sorted(list(numeros_acertados))}.")
else:
    print("\nQue pena! Você não acertou nenhum número desta vez.")

print("\nObrigado por jogar! Volte sempre.")
print()
print("-=" * 50)
print()