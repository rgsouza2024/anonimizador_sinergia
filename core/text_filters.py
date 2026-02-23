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
