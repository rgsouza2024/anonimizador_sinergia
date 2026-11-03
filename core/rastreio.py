"""Texto em transformacao que guarda, para cada caractere, o trecho do original de onde ele veio.

As fases de nome trocam trechos por marcadores (<NOME>, __NOME_PARTE_AUTORA__) uma depois da outra.
Sem rastreio, as posicoes da auditoria apontavam para o texto intermediario e as trocas de nome nao
eram registradas. Aqui cada troca fica registrada com a posicao no texto original.
"""

from array import array


class TextoRastreado:
    def __init__(self, texto):
        self.texto = texto or ""
        n = len(self.texto)
        self._inicio = array("l", range(n))
        self._fim = array("l", range(1, n + 1))
        self._marcador = bytearray(n)
        self.trocas = []

    def origem(self, inicio, fim):
        """Trecho do original (inicio, fim) que corresponde ao trecho [inicio, fim) do texto atual."""
        if inicio >= fim:
            if inicio < len(self._inicio):
                return self._inicio[inicio], self._inicio[inicio]
            ultimo = self._fim[-1] if len(self._fim) else 0
            return ultimo, ultimo
        return min(self._inicio[inicio:fim]), max(self._fim[inicio:fim])

    def dentro_de_marcador(self, inicio, fim):
        """O trecho do texto atual esta inteiro dentro de um marcador ja aplicado."""
        return fim > inicio and all(self._marcador[inicio:fim])

    def substituir(self, spans, valor):
        """Troca cada trecho [inicio, fim) do texto atual por `valor`; trechos sobrepostos sao ignorados."""
        if not spans:
            return
        partes, inicios, fins, marcador = [], array("l"), array("l"), bytearray()
        cursor = 0
        trocou = False
        for inicio, fim in sorted(spans):
            if inicio < cursor:
                continue
            partes.append(self.texto[cursor:inicio])
            inicios.extend(self._inicio[cursor:inicio])
            fins.extend(self._fim[cursor:inicio])
            marcador.extend(self._marcador[cursor:inicio])

            origem_inicio, origem_fim = self.origem(inicio, fim)
            partes.append(valor)
            inicios.extend([origem_inicio] * len(valor))
            fins.extend([origem_fim] * len(valor))
            marcador.extend(b"\x01" * len(valor))
            self.trocas.append({"inicio": origem_inicio, "fim": origem_fim, "valor": valor})
            cursor = fim
            trocou = True
        if not trocou:
            return
        partes.append(self.texto[cursor:])
        inicios.extend(self._inicio[cursor:])
        fins.extend(self._fim[cursor:])
        marcador.extend(self._marcador[cursor:])
        self.texto = "".join(partes)
        self._inicio, self._fim, self._marcador = inicios, fins, marcador
