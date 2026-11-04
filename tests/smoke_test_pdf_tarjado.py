"""Smoke test do PDF tarjado (endpoint /api/v1/pdf-tarjado de app.py)."""

import sys
from pathlib import Path

import fitz  # PyMuPDF
from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app  # noqa: E402

client = TestClient(app.fastapi_app)


def _pdf_de_teste():
    documento = fitz.open()
    pagina = documento.new_page()
    pagina.insert_text((72, 72), "AUTOR: JOAO PEDRO KOWALCZYK", fontsize=11)
    pagina.insert_text((72, 90), "CPF 926.511.422-72, telefone (62) 99876-5432.", fontsize=11)
    pagina.insert_textbox(
        fitz.Rect(72, 110, 420, 300),
        "Maria Aparecida Souza, residente na Rua Goiás, 45, Centro, requer o benefício assistencial "
        "à pessoa com deficiência em face do INSS, conforme a Lei 8.742/93. O autor Kowalczyk junta documentos.",
        fontsize=11,
        align=fitz.TEXT_ALIGN_JUSTIFY,
    )
    segunda = documento.new_page()
    segunda.insert_text((72, 72), "Página dois: testemunha Joana Wosniak compareceu.", fontsize=11)
    documento.set_metadata({
        "author": "JOAO PEDRO KOWALCZYK",
        "title": "Processo de Joao Pedro Kowalczyk",
        # Assuntos do PJe vêm no campo keywords e não são nomes de pessoa.
        "keywords": "DIREITO ASSISTENCIAL (12734) | Pessoa com Deficiência (11946)",
    })
    conteudo = documento.tobytes()
    documento.close()
    return conteudo


def test_pdf_tarjado():
    resposta = client.post(
        "/api/v1/pdf-tarjado",
        files={"file": ("peticao.pdf", _pdf_de_teste(), "application/pdf")},
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.headers["content-type"] == "application/pdf"
    assert "peticao_tarjado.pdf" in resposta.headers["content-disposition"]

    with fitz.open(stream=resposta.content, filetype="pdf") as tarjado:
        texto = "".join(pagina.get_text() for pagina in tarjado)
        metadados = tarjado.metadata
        assert tarjado.page_count == 2

    print("Texto que restou no PDF tarjado:\n" + texto)
    for sigiloso in ["KOWALCZYK", "Kowalczyk", "926.511.422-72", "5432", "Maria", "Aparecida", "Souza", "Goiás, 45", "Wosniak"]:
        assert sigiloso not in texto, f"'{sigiloso}' continua no PDF tarjado"
    for publico in ["AUTOR:", "residente na", "benefício assistencial", "pessoa com deficiência", "INSS", "Lei 8.742/93", "Página dois", "compareceu"]:
        assert publico in texto, f"'{publico}' foi tarjado sem necessidade"
    assert not metadados.get("author") and not metadados.get("title"), metadados
    print("[OK] PDF tarjado: dados retirados, texto público preservado, metadados apagados.")


def test_pdf_tarjado_com_revisao():
    resposta = client.post(
        "/api/v1/pdf-tarjado",
        files={"file": ("peticao.pdf", _pdf_de_teste(), "application/pdf")},
        data={"nomes_manuais": ["INSS"], "nao_tarjar": ["Wosniak", "926.511.422-72"]},
    )
    assert resposta.status_code == 200, resposta.text
    with fitz.open(stream=resposta.content, filetype="pdf") as tarjado:
        texto = "".join(pagina.get_text() for pagina in tarjado)
    assert "INSS" not in texto, "Nome manual continua no PDF tarjado"
    assert "Wosniak" in texto and "926.511.422-72" in texto, "Trecho marcado como 'nao_tarjar' foi tarjado"
    assert "KOWALCZYK" not in texto, "O restante deixou de ser tarjado"
    print("[OK] PDF tarjado respeita nomes_manuais e nao_tarjar.")


def _pdf_fatiado():
    """Página gravada em 3 recortes verticais sobrepostos, como em petições geradas por certos editores."""
    origem = fitz.open()
    pagina_origem = origem.new_page()
    linhas = [
        "AUTOR: JOAO PEDRO KOWALCZYK",
        "brasileiro, solteiro, portador do CPF 926.511.422-72, residente na cidade de Goiânia,",
        "a presente ação em face do INSS, conforme os fatos a seguir narrados.",
        "O autor Kowalczyk trabalhou como eletricista por vinte anos seguidos.",
        "A perícia médica constatou a incapacidade total para o trabalho.",
        "Requer a concessão do benefício desde a data do requerimento.",
    ]
    for i, linha in enumerate(linhas):
        pagina_origem.insert_text((72, 100 + 20 * i), linha, fontsize=11)
    documento = fitz.open()
    pagina = documento.new_page()
    largura = pagina.rect.width
    for x0, x1 in ((0, 220), (214, 390), (384, largura)):
        recorte = fitz.Rect(x0, 0, x1, pagina.rect.height)
        pagina.show_pdf_page(recorte, origem, 0, clip=recorte)
    conteudo = documento.tobytes()
    documento.close()
    origem.close()
    return conteudo


def test_pdf_fatiado():
    from core.pdf_texto import texto_da_pagina

    conteudo = _pdf_fatiado()
    with fitz.open(stream=conteudo, filetype="pdf") as documento:
        assert "portador do CPF 926.511.422-72" not in documento[0].get_text(), "O PDF de teste não ficou fatiado"
        texto, _ = texto_da_pagina(documento[0])
    assert "AUTOR: JOAO PEDRO KOWALCZYK\n" in texto, texto
    assert "brasileiro, solteiro, portador do CPF 926.511.422-72, residente" in texto, texto

    resposta = client.post("/api/v1/pdf-tarjado", files={"file": ("fatiado.pdf", conteudo, "application/pdf")})
    assert resposta.status_code == 200, resposta.text
    with fitz.open(stream=resposta.content, filetype="pdf") as tarjado:
        texto_tarjado, _ = texto_da_pagina(tarjado[0])
    for sigiloso in ["KOWALCZYK", "Kowalczyk", "926.511", "422-72"]:
        assert sigiloso not in texto_tarjado, f"'{sigiloso}' continua no PDF fatiado tarjado"
    for publico in ["brasileiro", "INSS", "eletricista", "perícia"]:
        assert publico in texto_tarjado, f"'{publico}' foi tarjado sem necessidade"
    print("[OK] PDF fatiado em recortes: texto remontado e tarjado no lugar certo.")


def _pdf_com_paginas_nao_tarjaveis():
    """Página 1 normal; 2 digitalizada (imagem com rodapé); 3 com texto ilegível (códigos de controle,
    como as telas do registro civil gravadas com fonte sem tabela de caracteres)."""
    documento = fitz.open()
    normal = documento.new_page()
    normal.insert_text((72, 72), "AUTOR: JOAO PEDRO KOWALCZYK", fontsize=11)
    normal.insert_text((72, 90), "O autor requer o benefício.", fontsize=11)
    digitalizada = documento.new_page()
    imagem = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 80), False)
    imagem.clear_with(200)
    digitalizada.insert_image(fitz.Rect(40, 60, 560, 700), pixmap=imagem)
    digitalizada.insert_text((40, 780), "Num. 2269495045 - Pág. 1", fontsize=8)
    ilegivel = documento.new_page()
    ilegivel.insert_text((72, 72), "".join(chr(i) for i in range(1, 31)) * 2, fontsize=11)
    conteudo = documento.tobytes()
    documento.close()
    return conteudo


def test_paginas_nao_tarjaveis():
    conteudo = _pdf_com_paginas_nao_tarjaveis()
    resposta = client.post("/api/v1/anonimizar-arquivo", files={"file": ("processo.pdf", conteudo, "application/pdf")})
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["paginas_nao_tarjaveis"] == {"texto_ilegivel": [3], "imagem": [2]}, resposta.json()

    sem_cobrir = client.post("/api/v1/pdf-tarjado", files={"file": ("processo.pdf", conteudo, "application/pdf")})
    assert sem_cobrir.headers["x-paginas-nao-tarjadas"] == "2,3"
    with fitz.open(stream=sem_cobrir.content, filetype="pdf") as tarjado:
        assert len(tarjado[1].get_images()) == 1, "Sem a opção, a página digitalizada deveria ficar como está"

    coberto = client.post(
        "/api/v1/pdf-tarjado",
        files={"file": ("processo.pdf", conteudo, "application/pdf")},
        data={"cobrir_paginas_nao_tarjaveis": "true"},
    )
    assert coberto.headers["x-paginas-nao-tarjadas"] == ""
    with fitz.open(stream=coberto.content, filetype="pdf") as tarjado:
        assert "requer o benefício" in tarjado[0].get_text() and "KOWALCZYK" not in tarjado[0].get_text()
        for indice in (1, 2):
            pagina = tarjado[indice]
            assert not pagina.get_images(), "Imagem continua na página coberta"
            assert pagina.get_text().startswith("Página coberta pelo anonimizador"), pagina.get_text()
    print("[OK] Páginas de imagem e de texto ilegível: informadas e, a pedido, cobertas por inteiro.")


def test_pdf_tarjado_texto_girado():
    # Extrato do CNIS impresso de lado: as linhas correm de baixo para cima numa página em pé.
    documento = fitz.open()
    pagina = documento.new_page()
    pagina.insert_text((72, 72), "Extrato previdenciário anexado aos autos.", fontsize=11)
    for x, linha in ((120, "CPF: 529.982.247-25"), (140, "Nome: JOAO PEDRO KOWALCZYK")):
        pagina.insert_text((x, 700), linha, fontsize=10, rotate=90)
    conteudo = documento.tobytes()

    resposta = client.post("/api/v1/pdf-tarjado", files={"file": ("cnis.pdf", conteudo, "application/pdf")})
    assert resposta.status_code == 200, resposta.text
    with fitz.open(stream=resposta.content, filetype="pdf") as tarjado:
        texto = tarjado[0].get_text()
    assert "Extrato previdenciário anexado aos autos." in texto, texto
    for dado in ("529.982", "247-25", "JOAO PEDRO", "KOWALCZYK"):
        assert dado not in texto, f"{dado} continua no PDF tarjado: {texto!r}"
    print("[OK] Texto girado: a tarja segue a direção da linha.")


def test_pdf_tarjado_recusa_outro_formato():
    resposta = client.post("/api/v1/pdf-tarjado", files={"file": ("peca.docx", b"x", "application/octet-stream")})
    assert resposta.status_code == 400
    print("[OK] Formato diferente de PDF recusado com 400.")


if __name__ == "__main__":
    test_pdf_tarjado()
    test_pdf_tarjado_com_revisao()
    test_pdf_fatiado()
    test_paginas_nao_tarjaveis()
    test_pdf_tarjado_texto_girado()
    test_pdf_tarjado_recusa_outro_formato()
    print("TODOS OS TESTES DO PDF TARJADO PASSARAM COM SUCESSO!")
