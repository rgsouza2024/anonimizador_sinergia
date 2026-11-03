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
        self._protegido = bytearray(n)
        self.trocas = []

    def proteger(self, spans):
        """Marca trechos do texto atual que nenhuma troca pode alterar ("nao tarjar")."""
        for inicio, fim in spans:
            self._protegido[inicio:fim] = b"\x01" * (fim - inicio)

    def toca_protegido(self, inicio, fim):
        return any(self._protegido[inicio:fim])

    def _sem_protegidos(self, inicio, fim):
        """Pedacos do trecho fora dos caracteres protegidos, sem espaco nas pontas e com alguma letra ou digito."""
        pedacos, atual = [], None
        for i in range(inicio, fim + 1):
            livre = i < fim and not self._protegido[i]
            if livre and atual is None:
                atual = i
            elif not livre and atual is not None:
                pedacos.append((atual, i))
                atual = None
        resultado = []
        for a, b in pedacos:
            while a < b and self.texto[a].isspace():
                a += 1
            while b > a and self.texto[b - 1].isspace():
                b -= 1
            if any(c.isalnum() for c in self.texto[a:b]):
                resultado.append((a, b))
        return resultado

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
        """Troca cada trecho [inicio, fim) do texto atual por `valor`; trechos sobrepostos sao ignorados.

        Caracteres protegidos nunca sao trocados: o trecho que os toca e recortado em volta deles
        ("Joao Lima" com "Lima" protegido troca so "Joao").
        """
        if not spans:
            return
        if any(self._protegido):
            spans = [pedaco for inicio, fim in spans for pedaco in self._sem_protegidos(inicio, fim)]
        partes, inicios, fins, marcador, protegido = [], array("l"), array("l"), bytearray(), bytearray()
        cursor = 0
        trocou = False
        for inicio, fim in sorted(spans):
            if inicio < cursor:
                continue
            partes.append(self.texto[cursor:inicio])
            inicios.extend(self._inicio[cursor:inicio])
            fins.extend(self._fim[cursor:inicio])
            marcador.extend(self._marcador[cursor:inicio])
            protegido.extend(self._protegido[cursor:inicio])

            origem_inicio, origem_fim = self.origem(inicio, fim)
            partes.append(valor)
            inicios.extend([origem_inicio] * len(valor))
            fins.extend([origem_fim] * len(valor))
            marcador.extend(b"\x01" * len(valor))
            protegido.extend(bytes(len(valor)))
            self.trocas.append({"inicio": origem_inicio, "fim": origem_fim, "valor": valor})
            cursor = fim
            trocou = True
        if not trocou:
            return
        partes.append(self.texto[cursor:])
        inicios.extend(self._inicio[cursor:])
        fins.extend(self._fim[cursor:])
        marcador.extend(self._marcador[cursor:])
        protegido.extend(self._protegido[cursor:])
        self.texto = "".join(partes)
        self._inicio, self._fim, self._marcador, self._protegido = inicios, fins, marcador, protegido
