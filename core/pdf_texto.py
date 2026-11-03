"""Texto de uma pagina de PDF, usado pela extracao (app_services) e pelo PDF tarjado.

Ha PDFs em que cada linha esta gravada em pedacos: a pagina e uma pilha de recortes verticais, e o
page.get_text() devolve um recorte inteiro antes do seguinte ("nº346" num ponto do texto,
"6.765.385-53" muito depois), de modo que o CPF nunca aparece inteiro. Nessas paginas o texto e
remontado linha a linha pela posicao dos caracteres. As demais paginas usam page.get_text().
"""

import fitz  # PyMuPDF

# So o texto: sem os dados das imagens, que o rawdict traz por padrao e pesam em PDF com muitas imagens.
FLAGS_RAWDICT_SO_TEXTO = fitz.TEXTFLAGS_RAWDICT & ~fitz.TEXT_PRESERVE_IMAGES

# Pedacos da mesma linha que se tocam ou se sobrepoem; numa pagina com duas colunas de verdade ha
# um vao grande entre elas.
_TOLERANCIA_EMENDA = 1.0  # pontos
_MINIMO_EMENDAS = 5


def _pedacos(pagina):
    """Linhas do rawdict: (bloco, linha de base, x0, x1, [(caractere, x0, x1, base, tamanho)])."""
    pedacos = []
    for numero_bloco, bloco in enumerate(pagina.get_text("rawdict", flags=FLAGS_RAWDICT_SO_TEXTO)["blocks"]):
        if bloco.get("type") != 0:
            continue
        for linha in bloco["lines"]:
            caracteres = [
                (c["c"], c["bbox"][0], c["bbox"][2], c["origin"][1], span["size"])
                for span in linha["spans"]
                for c in span["chars"]
            ]
            if caracteres:
                base = caracteres[0][3]
                pedacos.append((numero_bloco, base, caracteres[0][1], caracteres[-1][2], caracteres))
    return pedacos


def _mesma_linha(base_a, base_b, tamanho):
    return abs(base_a - base_b) <= 0.3 * tamanho


def _pagina_fatiada(pedacos):
    emendas = 0
    ordenados = sorted(pedacos, key=lambda p: (round(p[1]), p[2]))
    for anterior, atual in zip(ordenados, ordenados[1:]):
        tamanho = anterior[4][-1][4]
        if (
            anterior[0] != atual[0]
            and _mesma_linha(anterior[1], atual[1], tamanho)
            and anterior[2] < atual[2] <= anterior[3] + _TOLERANCIA_EMENDA
        ):
            emendas += 1
    return emendas >= _MINIMO_EMENDAS


def _remontar(pedacos):
    """Texto e caixas (x0, x1, base, tamanho) por caractere; quebra de linha recebe None."""
    linhas = []
    for pedaco in sorted(pedacos, key=lambda p: p[1]):
        tamanho = pedaco[4][0][4]
        if linhas and _mesma_linha(linhas[-1][0], pedaco[1], tamanho):
            linhas[-1][1].append(pedaco)
        else:
            linhas.append([pedaco[1], [pedaco]])

    texto, caixas = [], []
    for _, pedacos_linha in linhas:
        fim_atual = None
        for _, _, _, _, caracteres in sorted(pedacos_linha, key=lambda p: p[2]):
            for c, x0, x1, base, tamanho in caracteres:
                if fim_atual is not None:
                    # A letra da emenda aparece nos dois recortes ("OLIVEIR[A]" e "[A] DOS").
                    if (x0 + x1) / 2 < fim_atual:
                        continue
                    if x0 - fim_atual > 0.25 * tamanho and texto and texto[-1] != " " and c != " ":
                        texto.append(" ")
                        caixas.append((fim_atual, x0, base, tamanho))
                texto.append(c)
                caixas.append((x0, x1, base, tamanho))
                fim_atual = x1
        texto.append("\n")
        caixas.append(None)
    return "".join(texto), caixas


def texto_da_pagina(pagina):
    """(texto, caixas). Caixas e None quando o texto e o de page.get_text()."""
    pedacos = _pedacos(pagina)
    if _pagina_fatiada(pedacos):
        return _remontar(pedacos)
    return pagina.get_text(), None
