"""Shared configuration constants for the anonymization engine."""

NOME_ARQUIVO_SOBRENOMES = "nomes_comuns.txt"
NOME_ARQUIVO_TERMOS_COMUNS = "termos_comuns.txt"
NOME_ARQUIVO_TITULOS = "titulos_legais.txt"
LOGO_FILE_PATH = "Logo Projeto Sinergia TRF1 - Fundo Transparente.png"
ESTADO_VAZIO_TEXTO_ANONIMIZADO = "O texto anonimizado aparecera aqui apos clicar em 'Anonimizar texto'."
ESTADO_VAZIO_PDF_ORIGINAL = "O texto extraido do PDF sera exibido aqui apos o processamento."
ESTADO_VAZIO_PDF_ANONIMIZADO = "O resultado anonimizado do PDF sera exibido aqui apos o processamento."
COLUNAS_ENTIDADES_DETECTADAS = ["Entidade", "Texto Detectado", "Inicio", "Fim", "Score"]
RESUMO_VAZIO_TEXTO = "**Resumo:** aguardando processamento do texto."
RESUMO_VAZIO_PDF = "**Resumo:** aguardando processamento do PDF."
LIMITE_PDF_MB = 40
LIMITE_PDF_PAGINAS = 500
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
# Papeis do processo penal: o nome vira <NOME> (e nao <NOME_PARTE_AUTORA>, que nao serve
# para vitima ou testemunha).
PAPEIS_PROCESSO_PENAL = [
    "PACIENTE", "PACIENTES", "IMPETRANTE", "AGRAVANTE", "AGRAVADO", "AGRAVADA", "EMBARGANTE", "EMBARGADO",
    "EMBARGADA", "ACUSADO", "ACUSADA", "DENUNCIADO", "DENUNCIADA", "RÉU", "REU", "RÉ", "CORRÉU", "CORREU",
    "INVESTIGADO", "INVESTIGADA", "VÍTIMA", "VITIMA", "OFENDIDO", "OFENDIDA", "APENADO", "APENADA",
    "SENTENCIADO", "SENTENCIADA", "CONDENADO", "CONDENADA", "REPRESENTADO", "REPRESENTADA", "INTERESSADO",
    "INTERESSADA", "QUERELANTE", "QUERELADO", "QUERELADA", "ASSISTENTE DE ACUSAÇÃO", "TESTEMUNHA", "MENOR",
    "ADOLESCENTE",
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
    "INSS",
    "TRF",
    "PJE",
]
PALAVRAS_NAO_NOME_GENERICAS = [
    "PODER", "JUDICIARIO", "JUSTICA", "FEDERAL", "SECAO", "VARA", "PROCESSO",
    "BENEFICIO", "ASSISTENCIAL", "PRESTACAO", "CONTINUADA", "SENTENCA", "CONTESTACAO",
    "TURMA", "RECURSAL", "TRIBUNAL", "REGIAO", "DOCUMENTO", "ASSINADO", "ELETRONICAMENTE",
    "ADVOCACIA", "PROCURADORIA", "INSS", "MINISTERIO", "PUBLICO", "DEFENSORIA", "UNIAO",
    "DANO", "MORAL", "COLETIVO", "INTERINO", "RESIDUAL", "ENRIQUECIMENTO", "ILICITO",
    "OBRIGACAO", "REPARACAO", "INDENIZACAO",
]
BLOQUEIO_SEMANTICO_NOME = [
    # Classe/campos processuais
    "ASSUNTO", "ASSUNTOS", "CLASSE", "NUMERO", "ORGAO", "JULGADOR", "DISTRIBUICAO",
    "PROCESSO", "DOCUMENTO", "PARTES", "POLO", "ATIVO", "PASSIVO", "INTERNO",
    # Termos juridicos/previdenciarios recorrentes
    "BENEFICIO", "BENEFICIOS", "ASSISTENCIAL", "PRESTACAO", "CONTINUADA",
    "APOSENTADORIA", "RECURSO", "SENTENCA", "CONTESTACAO", "REPLICA", "PETICAO",
    "REQUERIMENTO", "REQUERIDA", "REQUERENTE", "RECORRENTE", "RECORRIDO",
    "DEFICIENCIA", "INCAPACIDADE", "MISERABILIDADE", "CARACTERIZACAO",
    # Estruturas e instituicoes que costumam aparecer em cabecalhos
    "PODER", "JUDICIARIO", "JUSTICA", "FEDERAL", "SECAO", "SUBSECAO", "VARA",
    "TURMA", "RECURSAL", "TRIBUNAL", "REGIAO", "AUTARQUIA", "INSTITUTO",
    "NACIONAL", "SEGURO", "SOCIAL", "INSS", "PJE", "PROCURADORIA", "ADVOCACIA",
    # Ruido comum de OCR/cabecalho
    "TIPO", "LAUDO", "PERICIAL", "ESTUDO", "SOCIOECONOMICO", "QUESITOS",
]
REGEX_UF_BR = r"(?:AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)"
# Palavras de uso comum que tambem sao sobrenomes: em bloco todo em maiusculas so sao
# tarjadas se estiverem coladas a outro nome ("7 (SETE) FATOS" fica; "JOSE SETE" sai).
PALAVRAS_COMUNS_CAIXA_ALTA = [
    "SETE", "ROSA", "LEAO", "PENA", "PRACA", "PORTO", "TERRA", "GUERRA", "LUZ", "PAZ", "PRADO", "MONTE", "MONTES",
    "PONTE", "ROCHA", "CRUZ", "FORTE", "NOBRE", "BRANCO", "CAMPOS", "SERRA", "LAGO", "LAGOA", "MATA", "MATO", "REIS",
    "NEVES", "BRASIL", "FONTES", "MINAS", "PARIS", "GATO", "LOBO", "HOMEM", "CABO", "BELO", "CASTELO", "CABECA",
    "GRILO", "MESTRE", "PASSOS", "QUINTA", "OURO", "ESTRELA", "FRADE", "FERRO", "FIGUEIRA", "MADEIRA", "VELHO",
    "VIEIRA", "SALES", "PEDROSA", "PEDROSO", "FRANCA", "BARATA", "CHAVES", "GUEDES", "MOURA", "PAIS", "PAES", "SA",
    "TORRES", "PRATES", "VARGAS", "VEIGA", "VENTURA", "BRAGA", "BANDEIRA", "LEAL", "COSTA", "MOTA", "PINTO",
    "MACHADO", "AMADO", "BENTO", "JARDIM", "LIMA", "SOUTO", "SANTOS",
]
# Capital de nome composto que tambem e nome de pessoa: nao e protegida como lugar.
CAPITAIS_COMPOSTAS_NAO_PROTEGIDAS = ["João Pessoa"]
