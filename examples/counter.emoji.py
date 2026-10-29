# tongue: emoji
# Emoji Python Example

🏛️ Contador:
    🔨 __init__(self, inicio=0):
        self.valor = inicio

    🔨 incrementar(self, paso=1):
        self.valor += paso
        📦 self.valor

    🔨 es_par(self):
        ❓ (self.valor % 2) == 0:
            📦 ✅
        ❗:
            📦 ❌

c = Contador(10)
nuevo_valor = c.incrementar(4)
par = c.es_par()
📢(f"Contador: {nuevo_valor}, Es par: {par}")
