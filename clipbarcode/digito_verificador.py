def mod10(dados):
    fatores = [2, 1]  # [2, 1]
    multiplicador = [
        fatores[i % len(fatores)] for i in range(len(dados))
    ]  # [2, 1, 2, 1, 2, 1,...] só que está da esquerda para direita nesse caso
    multiplicador = multiplicador[::-1]  # Agora sim, está da direita para esquerda!

    # ---------------------------------------------------------------------------
    digitos = []

    for i in range(len(multiplicador)):
        produto = int(dados[i]) * multiplicador[i]
        digitos += [
            int(i) for i in str(produto)
        ]  # Separando dígitos do resultado da múltiplicação (resultado = 18 --> 1+8,)

    soma = sum(digitos)

    # ---------------------------------------------------------------------------
    resto = soma % 10

    if resto == 0:  # Observação: Utilizar o dígito "0" para o resto 0 (zero). Exemplo:
        dv = 0
    else:
        dv = 10 - resto

    # ---------------------------------------------------------------------------
    return str(dv)


def mod11(dados, x10=False):
    fatores = [i for i in range(2, 10)]  # [2, 3, 4, 5, 6, 7, 8, 9]
    multiplicador = [
        fatores[i % len(fatores)] for i in range(len(dados))
    ]  # [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5, 6, 7, 8, 9,...] só que está da esquerda para direita nesse caso
    multiplicador = multiplicador[::-1]  # Agora sim, está da direita para esquerda!

    # ---------------------------------------------------------------------------
    soma = 0

    # print(dados, multiplicador)
    for i in range(len(multiplicador)):
        produto = int(dados[i]) * multiplicador[i]
        # print(f'{i:02}) {int(dados[i])} x {multiplicador[i]} = {produto:02} --> Soma antes: {soma:03}')
        soma += produto
    # print(f"Soma: {soma:03}")

    # ---------------------------------------------------------------------------
    resto = soma % 11
    # print(f"RESTO: {resto}")

    if x10:
        dv = ((soma * 10) % 11) % 10
    else:
        if (
            resto <= 1 or resto >= 10
        ):  # Observação: para o código de barras, sempre que o resto for 0, 1 ou 10, deverá ser utilizado o dígito 1
            dv = 1
        else:
            dv = 11 - resto

    # ---------------------------------------------------------------------------
    return str(dv)


# https://www.cjdinfo.com.br/solucao-javascript-calculo-digito-modulo-11?p=34
