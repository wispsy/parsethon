# tongue: es
# Ejemplo de Parsethon en Español

clase CalculadoraSecuencia:
    definir __init__(este, limite):
        este.limite = limite

    definir generar_fibonacci(este):
        a, b = 0, 1
        mientras a < este.limite:
            este.reportar(a)
            a, b = b, a + b
        retornar "Completado"

    definir reportar(este, valor):
        si valor > 10 y valor < 100:
            imprimir(f"Valor medio: {valor}")
        sino:
            imprimir(f"Valor: {valor}")

calc = CalculadoraSecuencia(50)
estado = calc.generar_fibonacci()
imprimir(f"Resultado final: {estado}")
