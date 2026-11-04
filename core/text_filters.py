"""Text extraction and filtering helpers for anonymization."""

import re
import unicodedata

from core.config import (
    BLOQUEIO_SEMANTICO_NOME,
    CAPITAIS_COMPOSTAS_NAO_PROTEGIDAS,
    PALAVRAS_COMUNS_CAIXA_ALTA,
    PALAVRAS_NAO_NOME_GENERICAS,
    PALAVRAS_NUNCA_NOME,
    PAPEIS_ALVO_NOME_PARTE,
    PAPEIS_PROCESSO_PENAL,
    PLACEHOLDER_NOME_PARTE_EXTERNO,
    PLACEHOLDER_NOME_PARTE_INTERNO,
    TERMOS_EXCLUSAO_NOME_PARTE,
    TERMOS_INDICADORES_PJ,
)
from core.rastreio import TextoRastreado
from core.resources import LISTA_ESTADOS_CAPITAIS_BR, LISTA_NOMES_COMUNS, LISTA_TERMOS_COMUNS, LISTA_TITULOS_LEGAIS


def _normalizar_texto_para_filtro(texto):
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    texto_sem_acentos = "".join(c for c in texto_normalizado if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto_sem_acentos).upper().strip()


_CONECTORES_NOME = {"DE", "DA", "DO", "DAS", "DOS", "E"}
_BLOQUEIO_SEMANTICO_NOME_NORMALIZADO = {
    _normalizar_texto_para_filtro(termo)
    for termo in (BLOQUEIO_SEMANTICO_NOME + PALAVRAS_NAO_NOME_GENERICAS + TERMOS_INDICADORES_PJ)
    if termo
}


def _trecho_bloqueado_semantico_para_nome(trecho):
    if not trecho:
        return False

    tokens = re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", trecho)
    if not tokens:
        return False

    tokens_relevantes = []
    for token in tokens:
        token_normalizado = _normalizar_token_nome(token)
        if not token_normalizado or token_normalizado in _CONECTORES_NOME:
            continue
        tokens_relevantes.append(token_normalizado)

    if not tokens_relevantes:
        return True

    qtd_bloqueados = sum(1 for token in tokens_relevantes if token in _BLOQUEIO_SEMANTICO_NOME_NORMALIZADO)
    if qtd_bloqueados == 0:
        return False

    if qtd_bloqueados == len(tokens_relevantes):
        return True

    if len(tokens_relevantes) >= 3 and (qtd_bloqueados / len(tokens_relevantes)) >= 0.75:
        return True

    return False


def _limpar_nome_extraido(candidato_nome):
    if not candidato_nome:
        return ""
    nome_limpo = re.sub(r"\s+", " ", candidato_nome).strip()
    nome_limpo = re.sub(r"\s+e\s+outros?\b.*$", "", nome_limpo, flags=re.IGNORECASE)
    nome_limpo = re.sub(r"\s*[-,:;]\s*$", "", nome_limpo).strip()
    return nome_limpo
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
            r"(?<!\w)[A-Z\u00C0-\u00DD][A-Z\u00C0-\u00DD0-9.&/\-]*(?:[^\S\n]+(?:DE|DA|DO|DAS|DOS|E|[A-Z\u00C0-\u00DD][A-Z\u00C0-\u00DD0-9.&/\-]*)){1,14}(?!\w)"
        ),
        re.compile(
            r"(?<!\w)[A-Z\u00C0-\u00DD][A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF0-9.&/\-]*(?:[^\S\n]+(?:de|da|do|das|dos|e|[A-Z\u00C0-\u00DD][A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF0-9.&/\-]*)){1,14}(?!\w)"
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


# Trechos que a varredura pela lista de nomes comuns nao deve tarjar.
_REGEX_MARIA_DA_PENHA = re.compile(r"(?i)\bMaria\s+da\s+Penha\b")
_REGEX_ORGAO_JULGADOR = re.compile(
    r"(?i)\b(?:Primeir|Segund|Terceir|Quart|Quint|Sext|S[ée]tim|Oitav|Non|D[ée]cim)[ao]"
    r"(?:\s+Primeir[ao]|\s+Segund[ao])?\s+(?:Turma\s+Recursal|Turma|Se[çc][ãa]o|C[âa]mara|Vara|Regi[ãa]o)\b"
)


def _spans_protegidos_lista_nomes(texto):
    """Lei Maria da Penha, orgao julgador ("Quinta Turma") e capital de nome composto ("Sao Paulo")."""
    spans = [m.span() for m in _REGEX_MARIA_DA_PENHA.finditer(texto)]
    spans += [m.span() for m in _REGEX_ORGAO_JULGADOR.finditer(texto)]
    for lugar in LISTA_ESTADOS_CAPITAIS_BR:
        if " " not in lugar or lugar in CAPITAIS_COMPOSTAS_NAO_PROTEGIDAS:
            continue
        spans += [m.span() for m in _compilar_regex_nome_flexivel(lugar).finditer(texto)]
    return spans


_PALAVRAS_COMUNS_CAIXA_ALTA_NORMALIZADAS = {_normalizar_token_nome(t) for t in PALAVRAS_COMUNS_CAIXA_ALTA}
# Estado de uma palavra so ("Bahia"): na lista, cada estado vem seguido da sigla ("Bahia", "BA").
_ESTADOS_UMA_PALAVRA_NORMALIZADOS = {
    _normalizar_token_nome(lugar)
    for lugar, seguinte in zip(LISTA_ESTADOS_CAPITAIS_BR, LISTA_ESTADOS_CAPITAIS_BR[1:])
    if " " not in lugar and len(lugar) > 2 and len(seguinte) == 2 and seguinte.isupper()
}
_REGEX_VIZINHO_DEPOIS = re.compile(r"[ \t ]+(?:(?:de|da|do|dos|das|e|DE|DA|DO|DOS|DAS|E)[ \t ]+)?")
_REGEX_VIZINHO_ANTES = re.compile(r"(?:[ \t ]+(?:de|da|do|dos|das|e|DE|DA|DO|DOS|DAS|E))?[ \t ]+$")
_PLACEHOLDERS_NOME = ("<NOME>", PLACEHOLDER_NOME_PARTE_INTERNO)


def _remover_comum_isolada_caixa_alta(texto, spans):
    """Palavra comum em linha toda em maiusculas, e nome de estado ("Jequié-Bahia"), so sao tarjados
    se colados a outro nome ("Maria Bahia")."""
    inicios = {inicio for inicio, _ in spans}
    fins = {fim for _, fim in spans}

    def tem_nome_vizinho(inicio, fim):
        depois = _REGEX_VIZINHO_DEPOIS.match(texto, fim, min(len(texto), fim + 12))
        if depois and (depois.end() in inicios or texto.startswith(_PLACEHOLDERS_NOME, depois.end())):
            return True
        antes = _REGEX_VIZINHO_ANTES.search(texto[max(0, inicio - 12):inicio])
        if antes:
            fim_vizinho = inicio - len(antes.group(0))
            if fim_vizinho in fins or texto[:fim_vizinho].endswith(_PLACEHOLDERS_NOME):
                return True
        return False

    def linha_toda_em_maiusculas(inicio, fim):
        inicio_linha = texto.rfind("\n", 0, inicio) + 1
        fim_linha = texto.find("\n", fim)
        linha = texto[inicio_linha:fim_linha if fim_linha >= 0 else len(texto)]
        return not any(c.islower() for c in linha)

    resultado = []
    for inicio, fim in spans:
        palavra = texto[inicio:fim]
        comum_em_caixa_alta = (
            len(palavra) >= 2
            and palavra == palavra.upper()
            and _normalizar_token_nome(palavra) in _PALAVRAS_COMUNS_CAIXA_ALTA_NORMALIZADAS
            and linha_toda_em_maiusculas(inicio, fim)
        )
        estado = _normalizar_token_nome(palavra) in _ESTADOS_UMA_PALAVRA_NORMALIZADOS
        if (comum_em_caixa_alta or estado) and not tem_nome_vizinho(inicio, fim):
            continue
        resultado.append((inicio, fim))
    return resultado


def _cortar_na_primeira_minuscula(nome):
    """Corta o nome antes da primeira palavra minuscula que nao e conector (de, da, do, das, dos, e).

    "Antonio Marcos Zwirtes apresentou defesa" vira "Antonio Marcos Zwirtes"; "foi condenado" vira "".
    """
    nome = nome or ""
    for match in re.finditer(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", nome):
        token = match.group(0)
        if token.upper() not in _CONECTORES_NOME and not token[0].isupper():
            nome = nome[:match.start()]
            break
    # Sem conector solto no fim ("Maria da") nem no comeco ("perito do Juízo" daria "do Juízo").
    nome = re.sub(r"^\s*(?:(?:de|da|do|das|dos|e|DE|DA|DO|DAS|DOS|E)\s+)+", "", nome)
    return re.sub(r"(?:\s+(?:de|da|do|das|dos|e|DE|DA|DO|DAS|DOS|E))+\s*$", "", nome).strip()


_REGEX_TIPO_LOGRADOURO = re.compile(
    r"(?i)\b(?:rua|ra|avenida|av|travessa|trav|alameda|pra[cç]a|rodovia|estrada|vicinal|bairro|setor|lote|quadra|qd"
    r"|cep|fazenda|s[ií]tio|ch[aá]cara)\b\.?"
)
_REGEX_FIM_DE_ENDERECO = re.compile(r"[;:!?\n()]|\.\s")
_MINUSCULAS_DE_ENDERECO = {"n", "s", "no", "km"}  # "nº 12", "s/n", "km 5"


def _token_esta_em_contexto_endereco(texto, inicio, fim, alcance=60):
    """A palavra faz parte de um endereco ("Rua Jose Silva", "Bairro Santa Maria").

    So conta o tipo de logradouro que vem ANTES da palavra, no mesmo trecho de endereco: entre os dois
    pode haver nomes, numeros, virgulas e conectores, mas palavra minuscula comum ("com", "requer"),
    ponto final ou ponto e virgula encerram o endereco. Antes, qualquer palavra a 40 caracteres de
    "Rua", para frente ou para tras, era poupada, e "Maria Silva, residente na Rua X" ficava a mostra.
    """
    trecho = texto[max(0, inicio - alcance):inicio]
    ultimo_tipo = None
    for ultimo_tipo in _REGEX_TIPO_LOGRADOURO.finditer(trecho):
        pass
    if ultimo_tipo is None:
        return False
    entre = trecho[ultimo_tipo.end():]
    if _REGEX_FIM_DE_ENDERECO.search(entre):
        return False
    for palavra in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", entre):
        if palavra[0].islower() and palavra.upper() not in _CONECTORES_NOME and palavra not in _MINUSCULAS_DE_ENDERECO:
            return False
    return True


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
    if _trecho_bloqueado_semantico_para_nome(nome_candidato):
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


def extrair_nomes_parte_alvo(texto_original, papeis=PAPEIS_ALVO_NOME_PARTE):
    nomes_encontrados = set()
    if not texto_original or not texto_original.strip():
        return nomes_encontrados

    papeis_regex = "|".join(re.escape(papel) for papel in papeis)

    padrao_linha_rotulo = re.compile(rf"(?im)^\s*({papeis_regex})\s*:\s*(.+?)\s*$")
    for match in padrao_linha_rotulo.finditer(texto_original):
        # "AUTOR: NOME, brasileiro, ..." -> o nome termina na primeira virgula.
        nome_limpo = _limpar_nome_extraido(match.group(2).split(",")[0])
        if _nome_parte_passa_filtros(nome_limpo):
            nomes_encontrados.add(nome_limpo)

    padrao_linha_partes = re.compile(rf"(?im)^\s*(.+?)\s*\(\s*({papeis_regex})\s*\)\s*$")
    for match in padrao_linha_partes.finditer(texto_original):
        nome_limpo = _limpar_nome_extraido(match.group(1))
        if _nome_parte_passa_filtros(nome_limpo):
            nomes_encontrados.add(nome_limpo)

    return nomes_encontrados


def extrair_nomes_papel_penal(texto_original):
    """Nome em linha propria com papel do processo penal ("AGRAVANTE: ...", "... (PACIENTE)")."""
    return extrair_nomes_parte_alvo(texto_original, PAPEIS_PROCESSO_PENAL)


def _nome_generico_passa_filtros(nome_candidato):
    if not _nome_parece_pessoa_fisica(nome_candidato):
        return False

    nome_normalizado = _normalizar_texto_para_filtro(nome_candidato)

    for termo in PALAVRAS_NAO_NOME_GENERICAS:
        if _contem_termo_normalizado(nome_normalizado, termo):
            return False

    return True


_CACHE_NOMES_COMUNS = {}


def _tem_nome_comum(trecho):
    if "nomes" not in _CACHE_NOMES_COMUNS:
        _CACHE_NOMES_COMUNS["nomes"] = _nomes_comuns_normalizados(LISTA_NOMES_COMUNS)
    nomes = _CACHE_NOMES_COMUNS["nomes"]
    return any(_normalizar_token_nome(t) in nomes for t in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", trecho))


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
        # Papeis do processo penal ("a vitima Fulana", "o paciente Fulano", "AGRAVANTE - Fulano").
        re.compile(
            rf"(?im)\b(?:PACIENTES?|IMPETRANTES?|AGRAVANTES?|AGRAVAD[OA]S?|EMBARGANTES?|EMBARGAD[OA]S?|"
            rf"ACUSAD[OA]S?|DENUNCIAD[OA]S?|R[ÉE]|CORR[ÉE]US?|INVESTIGAD[OA]S?|V[ÍI]TIMAS?|OFENDID[OA]S?|"
            rf"APENAD[OA]S?|SENTENCIAD[OA]S?|CONDENAD[OA]S?|QUERELANTES?|QUERELAD[OA]S?|TESTEMUNHAS?)\b"
            rf"\s*[:\-]?\s*(?P<nome>{bloco_nome})"
        ),
        # Parentes e representantes ("representado por sua genitora FULANA"). Filho/neto ficam
        # de fora porque tambem sao sobrenomes ("JOSE PEREIRA FILHO").
        re.compile(
            rf"(?im)\b(?:GENITOR(?:A|ES)?|M[ÃA]E|PAI|C[ÔO]NJUGE|COMPANHEIR[OA]|ESPOS[OA]|"
            rf"CURADOR(?:A)?|TUTOR(?:A)?|INSTITUIDOR(?:A)?|FALECID[OA]|DE\s+CUJUS)\b"
            rf"\s*[:\-]?\s*(?P<nome>{bloco_nome})"
        ),
    ]

    for padrao in padroes:
        for match in padrao.finditer(texto_original):
            # Os padroes rodam sem distinguir maiuscula (por causa do papel: "o reu"), o que fazia
            # "o reu foi condenado" virar nome; o nome termina na primeira palavra minuscula.
            nome_limpo = _limpar_nome_extraido(_cortar_na_primeira_minuscula(match.group("nome")))
            # Em caixa alta o corte acima nao funciona ("TESTEMUNHA OUVIDA EM JUIZO"): ali o nome
            # precisa ter ao menos uma palavra da lista de nomes comuns.
            if nome_limpo == nome_limpo.upper() and not _tem_nome_comum(nome_limpo):
                continue
            if _nome_generico_passa_filtros(nome_limpo):
                nomes_encontrados.add(nome_limpo)

    return nomes_encontrados


def aplicar_nomes_extraidos(rastreado, nomes_extraidos, placeholder):
    if not rastreado.texto or not nomes_extraidos:
        return
    for nome in sorted(nomes_extraidos, key=len, reverse=True):
        if not nome:
            continue
        nome_normalizado = re.sub(r"\s+", " ", nome).strip()
        tokens_nome = [token for token in nome_normalizado.split(" ") if token]
        if not tokens_nome:
            continue
        padrao_nome_flexivel = r"\s+".join(_token_para_regex_acento_flexivel(token) for token in tokens_nome)
        regex_nome = re.compile(rf"(?i)(?<!\w){padrao_nome_flexivel}(?!\w)")
        rastreado.substituir([m.span() for m in regex_nome.finditer(rastreado.texto)], placeholder)


def anonimizar_nomes_extraidos(texto, nomes_extraidos, placeholder):
    rastreado = TextoRastreado(texto)
    aplicar_nomes_extraidos(rastreado, nomes_extraidos, placeholder)
    return rastreado.texto if texto else texto


def _nomes_comuns_normalizados(lista_nomes_comuns):
    conectores = {"DE", "DA", "DO", "DAS", "DOS", "E"}
    termos_bloqueados = {
        _normalizar_token_nome(termo)
        for termo in PALAVRAS_NAO_NOME_GENERICAS + TERMOS_INDICADORES_PJ
        if termo and " " not in termo
    }
    nomes_normalizados = set()
    for item in lista_nomes_comuns or []:
        for token in re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", item or ""):
            token_normalizado = _normalizar_token_nome(token)
            if len(token_normalizado) < 3:
                continue
            if token_normalizado in conectores or token_normalizado in termos_bloqueados:
                continue
            nomes_normalizados.add(token_normalizado)
    return nomes_normalizados


# Palavras de um nome extraido que nunca sao propagadas sozinhas pelo documento.
_NAO_PROPAGAR_SOZINHA = _BLOQUEIO_SEMANTICO_NOME_NORMALIZADO | {
    _normalizar_texto_para_filtro(termo)
    for termo in TERMOS_EXCLUSAO_NOME_PARTE + PAPEIS_ALVO_NOME_PARTE + PAPEIS_PROCESSO_PENAL
    + ["FILHO", "FILHA", "NETO", "NETA", "JUNIOR", "SOBRINHO", "SOBRINHA", "OUTRO", "OUTROS", "OUTRA", "OUTRAS"]
}


def aplicar_sobrenomes_raros(rastreado, nomes_extraidos, lista_nomes_comuns, placeholder):
    rastreado.substituir(_spans_sobrenomes_raros(rastreado.texto, nomes_extraidos, lista_nomes_comuns), placeholder)


def anonimizar_sobrenomes_raros(texto, nomes_extraidos, lista_nomes_comuns, placeholder):
    rastreado = TextoRastreado(texto)
    aplicar_sobrenomes_raros(rastreado, nomes_extraidos, lista_nomes_comuns, placeholder)
    return rastreado.texto if texto else texto


def _spans_sobrenomes_raros(texto, nomes_extraidos, lista_nomes_comuns):
    """Tarja, onde aparecer sozinho, o sobrenome raro de um nome ja extraido.

    "AUTOR: JOSE KOWALCZYK DA SILVA" e depois "o autor Kowalczyk": a lista de nomes comuns nao
    conhece "Kowalczyk", que ficava a mostra. Vale para palavra com 4 letras ou mais, fora da lista
    de nomes comuns, e so quando escrita com maiuscula (o nome "Filho" nao leva "o filho" junto).
    """
    if not texto or not nomes_extraidos:
        return []

    nomes_comuns = _nomes_comuns_normalizados(lista_nomes_comuns)
    raros = set()
    for nome in nomes_extraidos:
        for token in re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", nome or ""):
            token_normalizado = _normalizar_token_nome(token)
            if len(token_normalizado) < 4 or token_normalizado in _CONECTORES_NOME:
                continue
            if token_normalizado in nomes_comuns or token_normalizado in _NAO_PROPAGAR_SOZINHA:
                continue
            raros.add(token_normalizado)
    if not raros:
        return []

    spans_substituicao = []
    for match in re.finditer(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", texto):
        inicio, fim = match.span()
        if not match.group(0)[0].isupper():
            continue
        # Nao mexer dentro de marcadores ja aplicados (<NOME>, __NOME_PARTE_AUTORA__).
        if inicio > 0 and texto[inicio - 1] in "<_":
            continue
        if fim < len(texto) and texto[fim] in ">_":
            continue
        if _normalizar_token_nome(match.group(0)) in raros:
            spans_substituicao.append((inicio, fim))
    return spans_substituicao


_REGEX_PALAVRA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")
_REGEX_SEPARADOR_NOME = re.compile(r"[ \t ]*\n?[ \t ]*")
_REGEX_FIM_DE_NOME_EM_CAIXA_ALTA = re.compile(r"\s*(?:[,.;:)\]]|\n|$)")


def _palavras_unicas_normalizadas(itens):
    resultado = set()
    for item in itens:
        tokens = _REGEX_PALAVRA.findall(item or "")
        if len(tokens) == 1:
            resultado.add(_normalizar_token_nome(tokens[0]))
    return resultado


# Palavras que a extensao de "nome inteiro" nunca absorve.
_NAO_ABSORVER_NO_NOME = (
    _NAO_PROPAGAR_SOZINHA
    | {_normalizar_token_nome(t) for t in PALAVRAS_NUNCA_NOME}
    | _palavras_unicas_normalizadas(LISTA_TERMOS_COMUNS)
    | _palavras_unicas_normalizadas(LISTA_TITULOS_LEGAIS)
    | {_normalizar_token_nome(t) for lugar in LISTA_ESTADOS_CAPITAIS_BR for t in _REGEX_PALAVRA.findall(lugar)}
)


def _estender_nome_inteiro(texto, spans, spans_protegidos):
    """Estende a tarja da lista de nomes comuns ao nome inteiro.

    A lista marca palavra por palavra, e o sobrenome que nao esta nela ficava a mostra no meio do
    nome ("<NOME> Schietti <NOME>"). Aqui:
    (1) palavra com maiuscula entre duas palavras da lista, na mesma sequencia de nome, entra na tarja;
    (2) nas pontas, ate duas palavras com maiuscula coladas ao nome entram tambem; em sequencia toda
        em maiusculas, so a ultima palavra antes de pontuacao ou fim de linha, porque ali a maiuscula
        nao indica nome;
    (3) a palavra recolhida assim (4 letras ou mais) e tarjada no documento inteiro.
    Cargos, tratamentos, termos do processo, lugares e palavras de organizacao nunca entram.
    """
    inicios_lista = {inicio for inicio, _ in spans}
    # Palavra que aparece com minuscula em outro ponto do texto e palavra comum ("compareceu"), nao nome.
    usadas_em_minuscula = {
        _normalizar_token_nome(m.group(0)) for m in _REGEX_PALAVRA.finditer(texto) if m.group(0)[0].islower()
    }
    palavras = []
    for match in _REGEX_PALAVRA.finditer(texto):
        inicio, fim = match.span()
        palavra = match.group(0)
        normalizada = _normalizar_token_nome(palavra)
        dentro_de_marcador = (inicio > 0 and texto[inicio - 1] in "<_") or (fim < len(texto) and texto[fim] in ">_")
        anterior = texto[max(0, inicio - 40):inicio].rstrip(" \t ")
        if inicio in inicios_lista:
            classe = "lista"
        elif normalizada in _CONECTORES_NOME:
            classe = "conector"
        elif (
            palavra[0].isupper()
            and len(normalizada) >= 3
            and normalizada not in _NAO_ABSORVER_NO_NOME
            and normalizada not in usadas_em_minuscula
            and not dentro_de_marcador
            and not _intervalo_esta_em_spans(inicio, fim, spans_protegidos)
            and not _token_esta_em_contexto_endereco(texto, inicio, fim)
        ):
            classe = "maiuscula"
        else:
            classe = "outra"
        palavras.append(
            {
                "inicio": inicio,
                "fim": fim,
                "norm": normalizada,
                "classe": classe,
                "caixa_alta": len(palavra) > 1 and palavra == palavra.upper(),
                # Maiuscula de inicio de frase nao indica nome: a palavra e tarjada ali, mas nao propagada.
                "inicio_de_frase": not anterior or anterior[-1] in ".!?:;\n",
            }
        )

    # Sequencias de nome: palavras separadas so por espaco (no maximo uma quebra de linha).
    sequencias, atual = [], []
    for i, palavra in enumerate(palavras):
        separador = texto[palavras[i - 1]["fim"]:palavra["inicio"]] if i > 0 else ""
        colada = bool(separador) and _REGEX_SEPARADOR_NOME.fullmatch(separador) is not None
        if palavra["classe"] == "outra" or not colada:
            if atual:
                sequencias.append(atual)
            atual = []
        if palavra["classe"] != "outra":
            atual.append(palavra)
    if atual:
        sequencias.append(atual)

    novos, recolhidas = [], set()
    for sequencia in sequencias:
        indices_lista = [k for k, p in enumerate(sequencia) if p["classe"] == "lista"]
        if not indices_lista:
            continue
        primeiro, ultimo = indices_lista[0], indices_lista[-1]
        for p in sequencia[primeiro:ultimo + 1]:
            if p["classe"] == "maiuscula":
                novos.append((p["inicio"], p["fim"]))
                if not p["inicio_de_frase"]:
                    recolhidas.add(p["norm"])
        toda_em_caixa_alta = all(p["classe"] == "conector" or p["caixa_alta"] for p in sequencia)
        for direcao, partida in ((-1, primeiro), (1, ultimo)):
            k, pegou = partida + direcao, 0
            while 0 <= k < len(sequencia) and pegou < 2:
                p = sequencia[k]
                if p["classe"] == "conector":
                    k += direcao
                    continue
                if p["classe"] != "maiuscula":
                    break
                if toda_em_caixa_alta:
                    depois = texto[p["fim"]:p["fim"] + 3]
                    if direcao < 0 or k != len(sequencia) - 1 or not _REGEX_FIM_DE_NOME_EM_CAIXA_ALTA.match(depois):
                        break
                novos.append((p["inicio"], p["fim"]))
                if not p["inicio_de_frase"]:
                    recolhidas.add(p["norm"])
                pegou += 1
                k += direcao

    # A palavra recolhida vale para o documento inteiro.
    if recolhidas:
        for p in palavras:
            if p["classe"] == "maiuscula" and p["norm"] in recolhidas and len(p["norm"]) >= 4:
                novos.append((p["inicio"], p["fim"]))

    return sorted(set(spans) | set(novos))


def aplicar_lista_nomes_comuns(rastreado, lista_nomes_comuns, placeholder="<NOME>"):
    rastreado.substituir(_spans_lista_nomes_comuns(rastreado.texto, lista_nomes_comuns), placeholder)


def anonimizar_por_lista_nomes_comuns(texto, lista_nomes_comuns, placeholder="<NOME>"):
    rastreado = TextoRastreado(texto)
    aplicar_lista_nomes_comuns(rastreado, lista_nomes_comuns, placeholder)
    return rastreado.texto if texto else texto


def _spans_lista_nomes_comuns(texto, lista_nomes_comuns):
    if not texto or not lista_nomes_comuns:
        return []

    nomes_normalizados = _nomes_comuns_normalizados(lista_nomes_comuns)
    if not nomes_normalizados:
        return []

    spans_pj = _mesclar_spans(_extrair_spans_pessoa_juridica(texto) + _spans_protegidos_lista_nomes(texto))
    spans_substituicao = []
    for match in re.finditer(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", texto):
        inicio, fim = match.span()
        # Palavra que comeca com minuscula nao e nome ("a pena", "a rosa").
        if not match.group(0)[0].isupper():
            continue
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

    spans_substituicao = _remover_comum_isolada_caixa_alta(texto, spans_substituicao)
    return _estender_nome_inteiro(texto, spans_substituicao, spans_pj)


def spans_nomes_manuais(texto, nomes_manuais):
    """Ocorrencias dos nomes informados a mao ("Faltou algum nome?"), inteiros ou palavra solta.

    Valem em qualquer contexto (inclusive perto de endereco ou dentro de nome de pessoa juridica),
    sem diferenca de maiuscula ou acento.
    """
    spans = []
    for nome in nomes_manuais or []:
        regex = _compilar_regex_nome_flexivel(str(nome or "").strip())
        if regex is not None:
            spans.extend(m.span() for m in regex.finditer(texto or ""))
    return _mesclar_spans(spans)


def spans_nao_tarjar(texto, trechos_nao_tarjar):
    """Ocorrencias dos trechos que a pessoa mandou nao tarjar ("Retirar tarja"), em todo o documento.

    Trecho so com letras casa sem diferenca de maiuscula ou acento; trecho com digitos ("926.511.422-72")
    casa literalmente, com espacos flexiveis.
    """
    spans = []
    for trecho in trechos_nao_tarjar or []:
        trecho = re.sub(r"\s+", " ", str(trecho or "")).strip()
        if not trecho:
            continue
        if re.search(r"\d", trecho) or not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", trecho):
            regex = re.compile(r"\s+".join(re.escape(parte) for parte in trecho.split(" ")))
        else:
            regex = _compilar_regex_nome_flexivel(trecho)
        if regex is not None:
            spans.extend(m.span() for m in regex.finditer(texto or ""))
    return _mesclar_spans(spans)


# Nome de magistrado citado ("Relator: Min. FULANO", "Rel. Des. Fed. Fulano", "JUIZ FEDERAL FULANO"):
# agente publico no exercicio da funcao, nao e tarjado. O rotulo nao distingue maiuscula; o nome sim.
_ROTULO_MAGISTRADO = (
    r"(?i:Relator(?:a\b|\(a\)|\b)(?:\s+(?:p/|para\s+o|do)\s+ac[óo]rd[ãa]o)?"
    r"|Rel\.(?:\s+(?:p/|para\s+o|do)\s+ac[óo]rd[ãa]o)?"
    r"|Min\.|Ministr[oa](?:\(a\)|\b)"
    r"|Des\.(?:\s*Fed\.)?|Desembargador(?:a\b|\(a\)|\b)(?:\s+Federal\b)?"
    r"|Ju[íi]z(?:a|\(a\))?\s+Federal\b(?:\s+Convocad[oa]\b)?)"
)
_TOKEN_NOME_MAGISTRADO = r"(?:[A-ZÀ-Ý][A-Za-zÀ-ÖØ-öø-ÿ']+|[A-Z]\.)"
_REGEX_MAGISTRADO = re.compile(
    rf"(?:{_ROTULO_MAGISTRADO}\s*:?\s*)+"
    rf"(?P<nome>{_TOKEN_NOME_MAGISTRADO}(?:\s+(?:(?:de|da|do|das|dos|e|DE|DA|DO|DAS|DOS|E)\s+)?{_TOKEN_NOME_MAGISTRADO}){{0,7}})"
)
# Palavras que encerram o nome (orgao, data do julgamento) ou mostram que nao era nome ("JUIZ FEDERAL DO JUIZADO").
_FIM_NOME_MAGISTRADO = {
    "DE", "DA", "DO", "DAS", "DOS", "E", "DATA", "TURMA", "TRIBUNAL", "PLENO", "PLENARIO", "JUIZADO", "VARA",
    "SECAO", "SUBSECAO", "JULGAMENTO", "JULGADO", "PUBLICACAO", "DECISAO", "ORGAO", "NUM", "FEDERAL", "ESPECIAL",
}


def spans_magistrados_citados(texto):
    """Trechos com nome de magistrado logo depois do rotulo (relator, ministro, desembargador, juiz federal)."""
    spans = []
    for match in _REGEX_MAGISTRADO.finditer(texto or ""):
        inicio = match.start("nome")
        fim = inicio
        for token in re.finditer(r"\S+", match.group("nome")):
            if _normalizar_token_nome(token.group()) in _FIM_NOME_MAGISTRADO:
                if token.group().upper() in ("DE", "DA", "DO", "DAS", "DOS", "E") and fim > inicio:
                    continue  # conectivo no meio do nome: so conta se vier outro nome depois
                break
            fim = match.start("nome") + token.end()
        if fim > inicio:
            spans.append((inicio, fim))
    return _mesclar_spans(spans)


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


# Registro do STJ (2024/0123456-7) e numero CNJ, inclusive partido em duas linhas
# ("5046512-\n94.2016.4.04.7000"): os sete digitos nao sao SIAPE.
_REGEX_NUMEROS_PROCESSO = [
    re.compile(r"\b\d{4}/\d{7}-\d\b"),
    re.compile(r"\d{7}-\s*\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}"),
]


def filtrar_resultados_analise(resultados_analise, texto_analise):
    spans_numero_processo = [m.span() for regex in _REGEX_NUMEROS_PROCESSO for m in regex.finditer(texto_analise)]
    resultados_filtrados = []
    for resultado in resultados_analise:
        if resultado.entity_type == "SIAPE" and any(
            resultado.start < fim and resultado.end > inicio for inicio, fim in spans_numero_processo
        ):
            continue
        if resultado.entity_type == "SIAPE":
            # A detecção inclui o rótulo ("matrícula SIAPE nº"); só o número é tarjado.
            resultado.start = resultado.end - 7
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


def _candidato_metadado_e_pessoa(candidato):
    # Assuntos do PJe ("Pessoa com Deficiência (11946)", "Aposentadoria por
    # Incapacidade Permanente") têm código numérico ou palavra minúscula que
    # não é conector; nome de pessoa não tem.
    if re.search(r"\d", candidato):
        return False
    conectores = {"de", "da", "do", "das", "dos", "e"}
    for palavra in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", candidato):
        if palavra.islower() and palavra not in conectores:
            return False
    return _nome_parece_pessoa_fisica(candidato)


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
            if _candidato_metadado_e_pessoa(candidato):
                nomes.add(candidato)

        for segmento in re.split(r"[;\n|]", valor_campo):
            candidato = _limpar_candidato_nome_metadado(segmento)
            if _candidato_metadado_e_pessoa(candidato):
                nomes.add(candidato)

    return nomes


def _tokens_nome_para_variantes(nome):
    tokens = [t for t in re.findall(r"[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF]+", nome or "") if t]
    if not tokens:
        return []

    conectores = {"de", "da", "do", "das", "dos", "e"}
    variantes = set()

    nome_completo = " ".join(tokens)
    if not _trecho_bloqueado_semantico_para_nome(nome_completo):
        variantes.add(nome_completo)

    for tamanho in range(len(tokens), 1, -1):
        prefixo = tokens[:tamanho]
        palavras_reais = [t for t in prefixo if t.lower() not in conectores]
        if len(palavras_reais) < 2:
            continue
        variante_prefixo = " ".join(prefixo)
        variante_sem_conectores = " ".join(palavras_reais)
        if not _trecho_bloqueado_semantico_para_nome(variante_prefixo):
            variantes.add(variante_prefixo)
        if not _trecho_bloqueado_semantico_para_nome(variante_sem_conectores):
            variantes.add(variante_sem_conectores)

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
            if _trecho_bloqueado_semantico_para_nome(token):
                return ""
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
        trecho_encontrado = match.group(0)
        if _intervalo_esta_em_spans(inicio, fim, spans_pj):
            continue
        # Nome informado nos metadados vale sempre, inclusive perto de endereco.
        if _trecho_bloqueado_semantico_para_nome(trecho_encontrado):
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
    rastreado = TextoRastreado(texto)
    metricas = aplicar_nomes_pf_metadados(rastreado, nomes_pf_metadados, placeholder)
    texto_resultado = rastreado.texto if texto else texto
    if retornar_metricas:
        return texto_resultado, metricas
    return texto_resultado


def aplicar_nomes_pf_metadados(rastreado, nomes_pf_metadados, placeholder="<NOME>"):
    """Tarja os nomes de pessoa fisica vindos dos metadados do PDF; devolve as metricas da fase."""
    spans, metricas = _spans_nomes_pf_metadados(rastreado.texto, nomes_pf_metadados)
    rastreado.substituir(spans, placeholder)
    return metricas


def _spans_nomes_pf_metadados(texto, nomes_pf_metadados):
    metricas = {
        "metadado_nome_identificado": False,
        "metadado_nomes_pf_total": 0,
        "metadado_ocorrencias_forcadas": 0,
    }

    if not texto or not nomes_pf_metadados:
        return [], metricas

    nomes_filtrados = sorted(
        {_limpar_candidato_nome_metadado(nome) for nome in nomes_pf_metadados if _nome_parece_pessoa_fisica(nome)},
        key=len,
        reverse=True,
    )
    if not nomes_filtrados:
        return [], metricas

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
    metricas["metadado_ocorrencias_forcadas"] = len(spans_substituicao)
    return spans_substituicao, metricas
