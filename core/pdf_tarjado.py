"""Gera o PDF tarjado a partir do PDF original e dos trechos trocados pelo motor.

Usa a redacao do PyMuPDF: o texto debaixo da tarja e removido do arquivo (nao fica escondido sob um
retangulo), e o restante do PDF continua pesquisavel. Os metadados sao apagados.

As posicoes dos trechos referem-se ao texto extraido por extrair_texto_de_pdf (core/app_services.py),
que concatena texto_da_pagina() de cada pagina (core/pdf_texto.py).
"""

import fitz  # PyMuPDF

from core.pdf_texto import FLAGS_RAWDICT_SO_TEXTO, texto_da_pagina

# A caixa de cada caractere vai do topo das maiusculas ao fim das descendentes e pode invadir a linha
# vizinha. Por isso a REMOCAO usa uma faixa estreita no meio da letra (so toca a propria linha), e a
# tarja PINTADA, desenhada depois, tem a altura visual da letra.
_FAIXA_REMOCAO = (0.55, 0.05)  # acima e abaixo da linha de base, em fracao do tamanho da fonte
_FAIXA_TARJA = (0.80, 0.22)
_SEM_IMAGENS = getattr(fitz, "PDF_REDACT_IMAGE_NONE", 0)
_SEM_TRACOS = getattr(fitz, "PDF_REDACT_LINE_ART_NONE", 0)


def _caracteres_da_pagina(pagina):
    """Texto da pagina reconstruido caractere a caractere, com (x0, x1, linha de base, tamanho) de cada um.

    Quebra de linha recebe None.
    """
    texto, caixas = [], []
    for bloco in pagina.get_text("rawdict", flags=FLAGS_RAWDICT_SO_TEXTO)["blocks"]:
        if bloco.get("type") != 0:
            continue
        for linha in bloco["lines"]:
            for span in linha["spans"]:
                for caractere in span["chars"]:
                    texto.append(caractere["c"])
                    x0, _, x1, _ = caractere["bbox"]
                    caixas.append((x0, x1, caractere["origin"][1], span["size"]))
            texto.append("\n")
            caixas.append(None)
    return "".join(texto), caixas


def _faixa(x0, x1, base, tamanho, faixa):
    acima, abaixo = faixa
    return fitz.Rect(x0, base - acima * tamanho, x1, base + abaixo * tamanho)


def _tarjas(pagina, texto_pagina, trechos, caixas=None):
    """Lista de (retangulo de remocao, retangulo pintado) para os trechos da pagina.

    caixas vem de texto_da_pagina() quando a pagina foi remontada; senao, e reconstruida aqui.
    """
    texto_reconstruido = texto_pagina
    if caixas is None:
        texto_reconstruido, caixas = _caracteres_da_pagina(pagina)
    tarjas = []
    if texto_reconstruido == texto_pagina:
        for inicio, fim in trechos:
            atual = None  # [x0, x1, base, tamanho] da tarja em montagem nesta linha
            for caixa in caixas[inicio:fim] + [None]:
                if caixa is None:  # quebra de linha (ou fim do trecho): fecha a tarja desta linha
                    if atual is not None:
                        tarjas.append((_faixa(*atual, _FAIXA_REMOCAO), _faixa(*atual, _FAIXA_TARJA)))
                    atual = None
                    continue
                x0, x1, base, tamanho = caixa
                if atual is None:
                    atual = [x0, x1, base, tamanho]
                else:
                    atual = [min(atual[0], x0), max(atual[1], x1), max(atual[2], base), max(atual[3], tamanho)]
        return tarjas
    # Plano B (texto da pagina nao reconstruido): procura o trecho na pagina; pode tarjar a mais.
    for inicio, fim in trechos:
        for pedaco in texto_pagina[inicio:fim].split("\n"):
            if pedaco.strip():
                tarjas.extend((r, r) for r in pagina.search_for(pedaco.strip()))
    return tarjas


_AVISO_PAGINA_COBERTA = (
    "Página coberta pelo anonimizador: o conteúdo desta página (imagem ou texto ilegível) "
    "não pôde ser lido para tarjar."
)


def _cobrir_pagina(pagina):
    """Remove texto, imagens e desenhos da pagina inteira e a pinta de preto, com um aviso."""
    pagina.add_redact_annot(pagina.rect, fill=(0, 0, 0))
    pagina.apply_redactions(
        images=getattr(fitz, "PDF_REDACT_IMAGE_REMOVE", 2),
        graphics=getattr(fitz, "PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED", 2),
    )
    margem = 0.1 * pagina.rect.width
    caixa = fitz.Rect(margem, pagina.rect.height / 2 - 40, pagina.rect.width - margem, pagina.rect.height / 2 + 40)
    pagina.insert_textbox(caixa, _AVISO_PAGINA_COBERTA, fontsize=12, color=(1, 1, 1), align=fitz.TEXT_ALIGN_CENTER)


def gerar_pdf_tarjado(conteudo_pdf, trechos_tarjados, paginas_cobrir=()):
    """Devolve os bytes do PDF com tarja preta sobre cada trecho (inicio, fim) do texto extraido.

    paginas_cobrir: numeros (a partir de 1) das paginas cobertas por inteiro, por nao poderem ser
    tarjadas trecho a trecho (ver paginas_nao_tarjaveis em core/pdf_texto.py).
    """
    paginas_cobrir = set(paginas_cobrir or ())
    with fitz.open(stream=conteudo_pdf, filetype="pdf") as documento:
        deslocamento = 0
        for numero, pagina in enumerate(documento, start=1):
            texto_pagina, caixas = texto_da_pagina(pagina)
            fim_pagina = deslocamento + len(texto_pagina)
            if numero in paginas_cobrir:
                _cobrir_pagina(pagina)
                deslocamento = fim_pagina
                continue
            trechos_pagina = [
                (max(inicio, deslocamento) - deslocamento, min(fim, fim_pagina) - deslocamento)
                for inicio, fim in trechos_tarjados
                if inicio < fim_pagina and fim > deslocamento
            ]
            tarjas = _tarjas(pagina, texto_pagina, trechos_pagina, caixas) if trechos_pagina else []
            if tarjas:
                for remocao, _ in tarjas:
                    pagina.add_redact_annot(remocao, fill=False)
                pagina.apply_redactions(images=_SEM_IMAGENS, graphics=_SEM_TRACOS)
                for _, pintada in tarjas:
                    pagina.draw_rect(pintada, color=None, fill=(0, 0, 0))
            deslocamento = fim_pagina
        documento.set_metadata({})
        documento.del_xml_metadata()
        return documento.tobytes(garbage=4, deflate=True)
