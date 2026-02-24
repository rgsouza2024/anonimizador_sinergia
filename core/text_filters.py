"""Text extraction and filtering helpers for anonymization."""

import re
import unicodedata

from core.config import (
    PALAVRAS_NAO_NOME_GENERICAS,
    PAPEIS_ALVO_NOME_PARTE,
    PLACEHOLDER_NOME_PARTE_EXTERNO,
    PLACEHOLDER_NOME_PARTE_INTERNO,
    TERMOS_EXCLUSAO_NOME_PARTE,
    TERMOS_INDICADORES_PJ,
)


def _limpar_nome_extraido(candidato_nome):
    if not candidato_nome:
        return ""
    nome_limpo = re.sub(r"\s+", " ", candidato_nome).strip()
    nome_limpo = re.sub(r"\s+e\s+outros?\b.*$", "", nome_limpo, flags=re.IGNORECASE)
    nome_limpo = re.sub(r"\s*[-,:;]\s*$", "", nome_limpo).strip()
    return nome_limpo


def _normalizar_texto_para_filtro(texto):
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    texto_sem_acentos = "".join(c for c in texto_normalizado if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto_sem_acentos).upper().strip()


def _contem_termo_normalizado(texto_normalizado, termo_normalizado):
    padrao = re.compile(rf"(?<![A-Z0-9]){re.escape(termo_normalizado)}(?![A-Z0-9])")
    return bool(padrao.search(texto_normalizado))


_VARIANTES_CARACTERE = {
    "a": "aàáâãäå",
    "c": "cç",
    "e": "eèéêë",
    "i": "iìíîï",
    "n": "nñ",
    "o": "oòóôõö",
    "u": "uùúûü",
    "y": "yýÿ",
}


def _token_para_regex_acento_flexivel(token):
    partes = []
    for caractere in token:
        base = unicodedata.normalize("NFKD", caractere)
        base = "".join(c for c in base if not unicodedata.combining(c))
        base = base.lower()
        if base in _VARIANTES_CARACTERE:
            variantes = "".join(sorted(set(_VARIANTES_CARACTERE[base])))
            partes.append(f"[{re.escape(variantes)}]")
            continue
        partes.append(re.escape(caractere))
    return "".join(partes)


def _normalizar_token_nome(token):
    if not token:
        return ""
    token_normalizado = unicodedata.normalize("NFKD", token)
    token_sem_acentos = "".join(c for c in token_normalizado if not unicodedata.combining(c))
    return token_sem_acentos.upper().strip()


def _intervalo_esta_em_spans(inicio, fim, spans):
    for inicio_span, fim_span in spans:
        if inicio >= inicio_span and fim <= fim_span:
            return True
    return False


def _mesclar_spans(spans):
    if not spans:
        return []
    spans_ordenados = sorted(spans, key=lambda intervalo: intervalo[0])
    resultado = [spans_ordenados[0]]
    for inicio, fim in spans_ordenados[1:]:
        ultimo_inicio, ultimo_fim = resultado[-1]
        if inicio <= ultimo_fim:
            resultado[-1] = (ultimo_inicio, max(ultimo_fim, fim))
            continue
        resultado.append((inicio, fim))
    return resultado


def _extrair_spans_pessoa_juridica(texto):
    if not texto:
        return []

    padroes_pj = [
        re.compile(
            r"(?<!\w)[A-Z\u00C0-\u00DD][A-Z\u00C0-\u00DD0-9.&/\-]*(?:\s+(?:DE|DA|DO|DAS|DOS|E|[A-Z\u00C0-\u00DD][A-Z\u00C0-\u00DD0-9.&/\-]*)){1,14}(?!\w)"
        ),
        re.compile(
            r"(?<!\w)[A-Z\u00C0-\u00DD][A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF0-9.&/\-]*(?:\s+(?:de|da|do|das|dos|e|[A-Z\u00C0-\u00DD][A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF0-9.&/\-]*)){1,14}(?!\w)"
        ),
    ]
    termos_pj_normalizados = [_normalizar_texto_para_filtro(termo) for termo in TERMOS_INDICADORES_PJ if termo]
    spans = []
    for padrao in padroes_pj:
        for match in padrao.finditer(texto):
            trecho_normalizado = _normalizar_texto_para_filtro(match.group(0))
            if any(_contem_termo_normalizado(trecho_normalizado, termo_pj) for termo_pj in termos_pj_normalizados):
                spans.append((match.start(), match.end()))
    return _mesclar_spans(spans)


def _token_esta_em_contexto_endereco(texto, inicio, fim, alcance=40):
    inicio_contexto = max(0, inicio - alcance)
    fim_contexto = min(len(texto), fim + alcance)
    contexto = texto[inicio_contexto:fim_contexto]
    return bool(
        re.search(
            r"(?i)\b(?:endere[cç]o|rua|ra|avenida|av\.?|travessa|trav\.?|alameda|rodovia|estrada|vicinal|bairro|lote|quadra|qd\.?|cep|fazenda|s[ií]tio|ch[aá]cara)\b",
            contexto,
        )
    )


def _nome_parece_pessoa_fisica(nome_candidato):
    if not nome_candidato:
        return False
    if "<" in nome_candidato or ">" in nome_candidato:
        return False

    tokens_alfabeticos = re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", nome_candidato)
    if len(tokens_alfabeticos) < 2:
        return False

    nome_normalizado = _normalizar_texto_para_filtro(nome_candidato)
    for termo in TERMOS_INDICADORES_PJ:
        if _contem_termo_normalizado(nome_normalizado, termo):
            return False
    return True


def _nome_parte_passa_filtros(nome_candidato):
    if not _nome_parece_pessoa_fisica(nome_candidato):
        return False

    nome_normalizado = _normalizar_texto_para_filtro(nome_candidato)

    for termo in TERMOS_EXCLUSAO_NOME_PARTE:
        if _contem_termo_normalizado(nome_normalizado, termo):
            return False

    return True


def extrair_nomes_parte_alvo(texto_original):
    nomes_encontrados = set()
    if not texto_original or not texto_original.strip():
        return nomes_encontrados

    papeis_regex = "|".join(re.escape(papel) for papel in PAPEIS_ALVO_NOME_PARTE)

    padrao_linha_rotulo = re.compile(rf"(?im)^\s*({papeis_regex})\s*:\s*(.+?)\s*$")
    for match in padrao_linha_rotulo.finditer(texto_original):
        nome_limpo = _limpar_nome_extraido(match.group(2))
        if _nome_parte_passa_filtros(nome_limpo):
            nomes_encontrados.add(nome_limpo)

    padrao_linha_partes = re.compile(rf"(?im)^\s*(.+?)\s*\(\s*({papeis_regex})\s*\)\s*$")
    for match in padrao_linha_partes.finditer(texto_original):
        nome_limpo = _limpar_nome_extraido(match.group(1))
        if _nome_parte_passa_filtros(nome_limpo):
            nomes_encontrados.add(nome_limpo)

    return nomes_encontrados


def _nome_generico_passa_filtros(nome_candidato):
    if not _nome_parece_pessoa_fisica(nome_candidato):
        return False

    nome_normalizado = _normalizar_texto_para_filtro(nome_candidato)

    for termo in PALAVRAS_NAO_NOME_GENERICAS:
        if _contem_termo_normalizado(nome_normalizado, termo):
            return False

    return True


def extrair_nomes_pessoais_contextuais(texto_original):
    nomes_encontrados = set()
    if not texto_original or not texto_original.strip():
        return nomes_encontrados

    conectores_nome = r"(?:DE|DA|DO|DAS|DOS|E|de|da|do|das|dos|e)"
    bloco_nome = rf"[A-Z\u00C0-\u00DD][A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+(?:\s+{conectores_nome})?(?:\s+[A-Z\u00C0-\u00DD][A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+){{1,7}}"

    padroes = [
        re.compile(rf"(?im)^\s*(?P<nome>{bloco_nome})\s*,\s*(?:brasileir[oa]|solteir[oa]|casad[oa]|desempregad[oa]|portador[oa])\b"),
        re.compile(
            rf"(?im)\b(?:AUTOR(?:A)?|REQUERENTE|REQUERID[OA]S?|RECORRENTE|RECORRID[OA]S?|R[ÉE]U(?:S)?|PERIT[AO]|ADVOGAD[OA]|POLO\s+PASSIVO|FILIA[ÇC][ÃA]O|ASSINADO\s+ELETRONICAMENTE\s+POR)\s*[:\-]?\s*(?P<nome>{bloco_nome})"
        ),
        re.compile(rf"(?im)^\s*(?P<nome>{bloco_nome})\s*\(\s*(?:R[ÉE]U(?:S)?|REQUERID[OA]S?)\s*\)\s*$"),
        re.compile(rf"(?im)\(\s*[IVXLC]+\s*\)\s*(?P<nome>{bloco_nome})"),
    ]

    for padrao in padroes:
        for match in padrao.finditer(texto_original):
            nome_limpo = _limpar_nome_extraido(match.group("nome"))
            if _nome_generico_passa_filtros(nome_limpo):
                nomes_encontrados.add(nome_limpo)

    return nomes_encontrados


def anonimizar_nomes_extraidos(texto, nomes_extraidos, placeholder):
    if not texto or not nomes_extraidos:
        return texto
    texto_resultado = texto
    for nome in sorted(nomes_extraidos, key=len, reverse=True):
        if not nome:
            continue
        nome_normalizado = re.sub(r"\s+", " ", nome).strip()
        tokens_nome = [token for token in nome_normalizado.split(" ") if token]
        if not tokens_nome:
            continue
        padrao_nome_flexivel = r"\s+".join(_token_para_regex_acento_flexivel(token) for token in tokens_nome)
        regex_nome = re.compile(rf"(?i)(?<!\w){padrao_nome_flexivel}(?!\w)")
        texto_resultado = regex_nome.sub(placeholder, texto_resultado)
    return texto_resultado


def anonimizar_por_lista_nomes_comuns(texto, lista_nomes_comuns, placeholder="<NOME>"):
    if not texto or not lista_nomes_comuns:
        return texto

    conectores = {"DE", "DA", "DO", "DAS", "DOS", "E"}
    termos_bloqueados = {
        _normalizar_token_nome(termo)
        for termo in PALAVRAS_NAO_NOME_GENERICAS + TERMOS_INDICADORES_PJ
        if termo and " " not in termo
    }
    nomes_normalizados = set()
    for item in lista_nomes_comuns:
        for token in re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", item or ""):
            token_normalizado = _normalizar_token_nome(token)
            if len(token_normalizado) < 3:
                continue
            if token_normalizado in conectores or token_normalizado in termos_bloqueados:
                continue
            nomes_normalizados.add(token_normalizado)

    if not nomes_normalizados:
        return texto

    spans_pj = _extrair_spans_pessoa_juridica(texto)
    spans_substituicao = []
    for match in re.finditer(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", texto):
        inicio, fim = match.span()
        if _intervalo_esta_em_spans(inicio, fim, spans_pj):
            continue
        if _token_esta_em_contexto_endereco(texto, inicio, fim):
            continue
        if inicio > 0 and texto[inicio - 1] == "<":
            continue
        if fim < len(texto) and texto[fim] == ">":
            continue
        token_normalizado = _normalizar_token_nome(match.group(0))
        if token_normalizado in nomes_normalizados:
            spans_substituicao.append((inicio, fim))

    if not spans_substituicao:
        return texto

    partes = []
    cursor = 0
    for inicio, fim in spans_substituicao:
        if inicio < cursor:
            continue
        partes.append(texto[cursor:inicio])
        partes.append(placeholder)
        cursor = fim
    partes.append(texto[cursor:])
    return "".join(partes)


def normalizar_placeholders_nome_parte(texto):
    if not texto:
        return texto
    return texto.replace(PLACEHOLDER_NOME_PARTE_INTERNO, PLACEHOLDER_NOME_PARTE_EXTERNO)


def _extrair_apenas_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def cpf_tem_digitos_validos(texto_cpf):
    cpf = _extrair_apenas_digitos(texto_cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False

    soma_dv1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto_dv1 = soma_dv1 % 11
    dv1 = 0 if resto_dv1 < 2 else 11 - resto_dv1

    soma_dv2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto_dv2 = soma_dv2 % 11
    dv2 = 0 if resto_dv2 < 2 else 11 - resto_dv2

    return cpf[-2:] == f"{dv1}{dv2}"


def trecho_tem_contexto_cpf(texto_analise, inicio, fim, alcance=32):
    inicio_contexto = max(0, inicio - alcance)
    fim_contexto = min(len(texto_analise), fim + alcance)
    contexto = texto_analise[inicio_contexto:fim_contexto]
    return bool(re.search(r"(?i)\b(?:cpf|cin|carteira\s+de\s+identidade\s+nacional)\b", contexto))


def trecho_tem_contexto_oab(texto_analise, inicio, fim, alcance=96):
    inicio_contexto = max(0, inicio - alcance)
    fim_contexto = min(len(texto_analise), fim + alcance)
    contexto = texto_analise[inicio_contexto:fim_contexto]
    return bool(
        re.search(
            r"(?i)\b(?:advogad[oa]|procurador(?:ia)?|representante(?:s)?|polo\s+ativo|polo\s+passivo|oab|assinado\s+eletronicamente|subscr(?:eve|ito)|inscri[çc][aã]o)\b",
            contexto,
        )
    )


def filtrar_resultados_analise(resultados_analise, texto_analise):
    resultados_filtrados = []
    for resultado in resultados_analise:
        trecho_detectado = texto_analise[resultado.start:resultado.end]
        if resultado.entity_type in {"CPF", "CIN"}:
            cpf_valido = cpf_tem_digitos_validos(trecho_detectado)
            cpf_em_contexto = trecho_tem_contexto_cpf(texto_analise, resultado.start, resultado.end)
            if not cpf_valido and not cpf_em_contexto:
                continue
        if resultado.entity_type == "OAB_NUMBER":
            trecho_tem_oab = bool(re.search(r"(?i)\bOAB\b", trecho_detectado))
            if not trecho_tem_oab:
                if not trecho_tem_contexto_oab(texto_analise, resultado.start, resultado.end):
                    continue
        resultados_filtrados.append(resultado)
    return resultados_filtrados


def _nome_papel_metadado_regex():
    return (
        r"AUTOR(?:A)?|REQUERENTE|REQUERIDO(?:A)?|RECORRENTE|RECORRIDO(?:A)?|"
        r"EXEQUENTE|EXECUTADO(?:A)?|EXEQU[ÍI]DO(?:A)?|EXEQUENDO|EMBARGANTE|EMBARGADO(?:A)?"
    )


def _limpar_candidato_nome_metadado(valor):
    nome_limpo = _limpar_nome_extraido(valor or "")
    nome_limpo = re.sub(
        r"(?i)^\s*(?:dr\.?|dra\.?|sr\.?|sra\.?|des\.?|desembargador(?:a)?|ministro(?:a)?)\s+",
        "",
        nome_limpo,
    ).strip()
    nome_limpo = re.sub(r"\s+", " ", nome_limpo).strip(" -;:,")
    return nome_limpo


def extrair_nomes_pf_metadados_pdf(metadados_pdf):
    if not isinstance(metadados_pdf, dict) or not metadados_pdf:
        return set()

    nomes = set()
    campos_interesse = ["subject", "title", "author", "keywords"]
    papel_regex = _nome_papel_metadado_regex()

    for campo in campos_interesse:
        valor_campo = str(metadados_pdf.get(campo, "") or "")
        if not valor_campo.strip():
            continue

        padrao_papel = re.compile(rf"(?i)\b(?:{papel_regex})\s*:\s*([^;\n|]+)")
        for match in padrao_papel.finditer(valor_campo):
            candidato = _limpar_candidato_nome_metadado(match.group(1))
            if _nome_parece_pessoa_fisica(candidato):
                nomes.add(candidato)

        for segmento in re.split(r"[;\n|]", valor_campo):
            candidato = _limpar_candidato_nome_metadado(segmento)
            if _nome_parece_pessoa_fisica(candidato):
                nomes.add(candidato)

    return nomes


def _tokens_nome_para_variantes(nome):
    tokens = [t for t in re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", nome or "") if t]
    if not tokens:
        return []

    conectores = {"de", "da", "do", "das", "dos", "e"}
    variantes = set()

    nome_completo = " ".join(tokens)
    variantes.add(nome_completo)

    for tamanho in range(len(tokens), 1, -1):
        prefixo = tokens[:tamanho]
        palavras_reais = [t for t in prefixo if t.lower() not in conectores]
        if len(palavras_reais) < 2:
            continue
        variantes.add(" ".join(prefixo))
        variantes.add(" ".join(palavras_reais))

    return sorted(variantes, key=lambda x: len(x), reverse=True)


def _compilar_regex_nome_flexivel(texto_nome):
    tokens = [t for t in re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", texto_nome or "") if t]
    if not tokens:
        return None
    padrao_nome = r"\s+".join(_token_para_regex_acento_flexivel(token) for token in tokens)
    return re.compile(rf"(?i)(?<!\w){padrao_nome}(?!\w)")


def _extrair_primeiro_nome(nome):
    conectores = {"de", "da", "do", "das", "dos", "e"}
    for token in re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", nome or ""):
        if token.lower() not in conectores:
            return token
    return ""


def _tem_contexto_papel_processual(texto, inicio, fim, alcance=64):
    inicio_contexto = max(0, inicio - alcance)
    fim_contexto = min(len(texto), fim + alcance)
    contexto = texto[inicio_contexto:fim_contexto]
    return bool(
        re.search(
            r"(?i)\b(?:autor(?:a)?|requerente|requerid[oa]|recorrente|recorrid[oa]|réu|reu|executad[oa]|exequente|representante|advogad[oa]|perit[ao])\b",
            contexto,
        )
    )


def _coletar_spans_para_regex(texto, regex, spans_pj, exigir_contexto_processual=False):
    spans = []
    if regex is None:
        return spans

    for match in regex.finditer(texto):
        inicio, fim = match.span()
        if _intervalo_esta_em_spans(inicio, fim, spans_pj):
            continue
        if _token_esta_em_contexto_endereco(texto, inicio, fim):
            continue
        if inicio > 0 and texto[inicio - 1] == "<":
            continue
        if fim < len(texto) and texto[fim] == ">":
            continue
        if exigir_contexto_processual and not _tem_contexto_papel_processual(texto, inicio, fim):
            continue
        spans.append((inicio, fim))

    return spans


def anonimizar_nomes_pf_metadados(texto, nomes_pf_metadados, placeholder="<NOME>", retornar_metricas=False):
    metricas = {
        "metadado_nome_identificado": False,
        "metadado_nomes_pf_total": 0,
        "metadado_ocorrencias_forcadas": 0,
    }

    if not texto or not nomes_pf_metadados:
        if retornar_metricas:
            return texto, metricas
        return texto

    nomes_filtrados = sorted(
        {_limpar_candidato_nome_metadado(nome) for nome in nomes_pf_metadados if _nome_parece_pessoa_fisica(nome)},
        key=len,
        reverse=True,
    )
    if not nomes_filtrados:
        if retornar_metricas:
            return texto, metricas
        return texto

    metricas["metadado_nome_identificado"] = True
    metricas["metadado_nomes_pf_total"] = len(nomes_filtrados)

    spans_pj = _extrair_spans_pessoa_juridica(texto)
    spans_candidatos = []
    primeiros_nomes = [_normalizar_token_nome(_extrair_primeiro_nome(nome)) for nome in nomes_filtrados if _extrair_primeiro_nome(nome)]
    frequencia_primeiros_nomes = {}
    for primeiro in primeiros_nomes:
        frequencia_primeiros_nomes[primeiro] = frequencia_primeiros_nomes.get(primeiro, 0) + 1

    for nome in nomes_filtrados:
        for variante in _tokens_nome_para_variantes(nome):
            regex_variante = _compilar_regex_nome_flexivel(variante)
            spans_candidatos.extend(_coletar_spans_para_regex(texto, regex_variante, spans_pj))

        primeiro_nome = _extrair_primeiro_nome(nome)
        primeiro_normalizado = _normalizar_token_nome(primeiro_nome)
        if primeiro_nome and frequencia_primeiros_nomes.get(primeiro_normalizado, 0) == 1:
            padrao_curto = re.compile(
                rf"(?i)\b(?:sr\.?|sra\.?|senhor(?:a)?|dr\.?|dra\.?|des\.?|desembargador(?:a)?|ministro(?:a)?)\s+{_token_para_regex_acento_flexivel(primeiro_nome)}\b"
            )
            spans_candidatos.extend(
                _coletar_spans_para_regex(texto, padrao_curto, spans_pj, exigir_contexto_processual=False)
            )

    spans_substituicao = _mesclar_spans(spans_candidatos)
    if not spans_substituicao:
        if retornar_metricas:
            return texto, metricas
        return texto

    metricas["metadado_ocorrencias_forcadas"] = len(spans_substituicao)

    partes = []
    cursor = 0
    for inicio, fim in spans_substituicao:
        if inicio < cursor:
            continue
        partes.append(texto[cursor:inicio])
        partes.append(placeholder)
        cursor = fim
    partes.append(texto[cursor:])
    texto_resultado = "".join(partes)
    if retornar_metricas:
        return texto_resultado, metricas
    return texto_resultado
