"""Shared configuration constants for the anonymization engine."""

NOME_ARQUIVO_SOBRENOMES = "sobrenomes_comuns.txt"
NOME_ARQUIVO_TERMOS_COMUNS = "termos_comuns.txt"
NOME_ARQUIVO_TITULOS = "titulos_legais.txt"
LOGO_FILE_PATH = "Logo Projeto Sinergia TRF1 - Fundo Transparente.png"
ESTADO_VAZIO_TEXTO_ANONIMIZADO = "O texto anonimizado aparecera aqui apos clicar em 'Anonimizar texto'."
ESTADO_VAZIO_PDF_ORIGINAL = "O texto extraido do PDF sera exibido aqui apos o processamento."
ESTADO_VAZIO_PDF_ANONIMIZADO = "O resultado anonimizado do PDF sera exibido aqui apos o processamento."
COLUNAS_ENTIDADES_DETECTADAS = ["Entidade", "Texto Detectado", "Inicio", "Fim", "Score"]
RESUMO_VAZIO_TEXTO = "**Resumo:** aguardando processamento do texto."
RESUMO_VAZIO_PDF = "**Resumo:** aguardando processamento do PDF."
PLACEHOLDER_NOME_PARTE_EXTERNO = "<NOME_PARTE_AUTORA>"
PLACEHOLDER_NOME_PARTE_INTERNO = "__NOME_PARTE_AUTORA__"
PAPEIS_ALVO_NOME_PARTE = [
    "AUTOR",
    "AUTORA",
    "PARTE AUTORA",
    "RECORRENTE",
    "REQUERENTE",
    "RECORRIDO",
    "RECORRIDA",
]
TERMOS_EXCLUSAO_NOME_PARTE = [
    "ADVOGADO",
    "ADVOGADA",
    "OAB",
    "JUIZ",
    "JUIZA",
    "RELATOR",
    "PROCURADOR",
    "PROCURADORIA",
    "DESEMBARGADOR",
    "MINISTRO",
    "DEFENSOR",
    "PATRONO",
    "PATRONA",
    "TERCEIRO INTERESSADO",
]
TERMOS_INDICADORES_PJ = [
    "LTDA",
    "S/A",
    "EIRELI",
    "ME",
    "MEI",
    "EPP",
    "SPE",
    "CNPJ",
    "ONG",
    "OSCIP",
    "COOPERATIVA",
    "COMPANHIA",
    "INSTITUTO",
    "ASSOCIACAO",
    "SOCIEDADE",
    "EMPRESA",
    "FUNDACAO",
    "AUTARQUIA",
    "UNIAO",
    "MUNICIPIO",
    "ESTADO",
    "MINISTERIO",
    "SECRETARIA",
    "PREFEITURA",
    "TRIBUNAL",
    "DEFENSORIA",
    "PROCURADORIA",
    "MINISTERIO PUBLICO",
    "IBAMA",
    "ICMBIO",
]
PALAVRAS_NAO_NOME_GENERICAS = [
    "PODER", "JUDICIARIO", "JUSTICA", "FEDERAL", "SECAO", "VARA", "PROCESSO",
    "BENEFICIO", "ASSISTENCIAL", "PRESTACAO", "CONTINUADA", "SENTENCA", "CONTESTACAO",
    "TURMA", "RECURSAL", "TRIBUNAL", "REGIAO", "DOCUMENTO", "ASSINADO", "ELETRONICAMENTE",
    "ADVOCACIA", "PROCURADORIA", "INSS", "MINISTERIO", "PUBLICO", "DEFENSORIA", "UNIAO",
    "DANO", "MORAL", "COLETIVO", "INTERINO", "RESIDUAL", "ENRIQUECIMENTO", "ILICITO",
    "OBRIGACAO", "REPARACAO", "INDENIZACAO",
]
REGEX_UF_BR = r"(?:AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)"
