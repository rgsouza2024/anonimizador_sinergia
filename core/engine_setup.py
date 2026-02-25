"""Initialization/setup for Presidio analyzer and anonymizer engines."""

import re

import spacy
from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_analyzer.pattern import Pattern
from presidio_anonymizer import AnonymizerEngine

from core.config import REGEX_UF_BR


def carregar_analyzer_engine(
    termos_safe_location,
    termos_legal_header,
    lista_sobrenomes,
    termos_estado_civil,
    termos_organizacoes_conhecidas,
    termos_comuns_a_manter,
    titulos_legais,
):
    try:
        spacy.load("pt_core_news_lg")
    except OSError:
        print("ERRO CRÍTICO: Modelo spaCy 'pt_core_news_lg' não encontrado. Instale com: python -m spacy download pt_core_news_lg")
        return None

    spacy_engine_obj = SpacyNlpEngine(models=[{"lang_code": "pt", "model_name": "pt_core_news_lg"}])
    analyzer = AnalyzerEngine(nlp_engine=spacy_engine_obj, supported_languages=["pt"], default_score_threshold=0.4)

    if termos_safe_location:
        analyzer.registry.add_recognizer(
            PatternRecognizer(
                supported_entity="SAFE_LOCATION",
                name="SafeLocationRecognizer",
                deny_list=termos_safe_location,
                supported_language="pt",
                deny_list_score=0.99,
            )
        )
    if termos_legal_header:
        analyzer.registry.add_recognizer(
            PatternRecognizer(
                supported_entity="LEGAL_HEADER",
                name="LegalHeaderRecognizer",
                deny_list=termos_legal_header,
                supported_language="pt",
                deny_list_score=0.99,
            )
        )

    if titulos_legais:
        palavras_para_regex = "|".join(titulos_legais)
        legal_titles_pattern = Pattern(
            name="legal_title_pattern",
            regex=rf"(?i)\b({palavras_para_regex})(?:\([A-Z]\))?\b",
            score=1.0,
        )
        legal_title_recognizer = PatternRecognizer(
            supported_entity="LEGAL_TITLE",
            name="LegalTitleRecognizer",
            patterns=[legal_titles_pattern],
            supported_language="pt",
        )
        analyzer.registry.add_recognizer(legal_title_recognizer)

    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="CPF",
            name="CustomCpfRecognizer",
            patterns=[
                Pattern(name="cpf_formatado", regex=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", score=1.0),
                Pattern(name="cpf_com_separadores", regex=r"\b\d{3}[.\s]\d{3}[.\s]\d{3}[-\s]\d{2}\b", score=0.99),
                Pattern(name="cpf_com_rotulo", regex=r"(?i)\bCPF\s*(?:n[ºo°.]?\s*)?:?\s*\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", score=1.0),
                Pattern(name="cin_com_rotulo", regex=r"(?i)\bCIN\s*(?:n[ºo°.]?\s*)?:?\s*\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", score=1.0),
                Pattern(
                    name="carteira_identidade_nacional_com_numero",
                    regex=r"(?i)\bCarteira\s+de\s+Identidade\s+Nacional\b[\s:\-nºo°\.]{0,20}\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
                    score=0.99,
                ),
                Pattern(name="cpf_apenas_numeros", regex=r"(?<!\d)\d{11}(?!\d)", score=0.995),
            ],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="OAB_NUMBER",
            name="CustomOabRecognizer",
            patterns=[
                Pattern(
                    name="oab_uf_numero",
                    regex=rf"(?i)\bOAB\s*(?:n[º°.]?\s*)?(?:/|-)?\s*{REGEX_UF_BR}\s*(?:[Nn][º°o.\?]?\s*)?[-.]?\s*\d{{1,6}}(?:\.\d{{3}})?\b",
                    score=0.90,
                ),
                Pattern(
                    name="oab_numero_uf",
                    regex=rf"(?i)\bOAB\s*(?:n[º°.]?\s*)?\d{{1,6}}(?:\.\d{{3}})?\s*\/\s*{REGEX_UF_BR}\b",
                    score=0.88,
                ),
                Pattern(
                    name="oab_uf_numero_compacto",
                    regex=rf"(?i)\bOAB\s*(?:/|-)?\s*{REGEX_UF_BR}\s*[-.]?\s*\d{{4,6}}(?:\.\d{{3}})?\b",
                    score=0.80,
                ),
                Pattern(
                    name="oab_uf_numero_sem_prefixo",
                    regex=rf"(?i)(?<!/)\b{REGEX_UF_BR}\s*[-.]?\s*\d{{4,6}}(?:\.\d{{3}})?\b",
                    score=0.70,
                ),
            ],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="PHONE_NUMBER_BR",
            name="CustomPhoneBrRecognizer",
            patterns=[
                Pattern(
                    name="telefone_com_ddd",
                    regex=r"(?<!\d)(?:\(?\d{2}\)?\s*)(?:9\d{4}|\d{4})[-\s]\d{4}(?!\d)",
                    score=0.93,
                ),
                Pattern(
                    name="telefone_sem_ddd",
                    regex=r"(?<!\d)(?:9\d{4}|\d{4})-\d{4}(?!\d)",
                    score=0.92,
                ),
            ],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="CEP_NUMBER",
            name="CustomCepRecognizer",
            patterns=[
                Pattern(name="cep_com_rotulo", regex=r"(?i)\bCEP\s*[:\-]?\s*\d{5}-?\d{3}\b", score=0.99),
                Pattern(name="cep_hifen", regex=r"\b\d{5}-\d{3}\b", score=0.93),
                Pattern(name="cep_pontuado", regex=r"\b\d{2}\.\d{3}-\d{3}\b", score=0.93),
            ],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="ENDERECO_LOGRADOURO",
            name="EnderecoLogradouroRecognizer",
            patterns=[
                Pattern(
                    name="logradouro_com_numero_e_complemento",
                    regex=r"(?i)\b(?:rua|ra|avenida|av\.?|travessa|trav\.?|alameda|pra[cç]a|rodovia|estrada)\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]+){0,8}\s*,\s*(?:n[ºo°.]?\s*)?\d+[A-Za-z0-9/\-]*\s*,\s*[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]{2,}(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]{2,}){0,5}",
                    score=0.97,
                ),
                Pattern(
                    name="logradouro_prefixado",
                    regex=r"(?i)\b(?:rua|ra|avenida|av\.?|travessa|trav\.?|alameda|pra[cç]a|rodovia|estrada|vicinal)\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]+){0,8}(?:\s*,?\s*(?:n[ºo°.]?\s*)?\d+[A-Za-z0-9/\-]*)?(?:\s*,\s*[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]{2,}(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]{2,}){0,5})?",
                    score=0.90,
                ),
                Pattern(
                    name="beco_viela_ramal_com_numero",
                    regex=r"(?i)\b(?:beco|viela|ramal|ladeira|passagem)\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´\-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´\-]+){0,6}\s*,\s*(?:casa\s*)?\d+[A-Za-z0-9/\-]*(?:\s*,?\s*(?:bairro\s*:?\s*)?[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´\-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´\-]+){0,4})?",
                    score=0.98,
                ),
                Pattern(name="vicinal_composta", regex=r"(?i)\bVicinal\s+\d{1,3}\s+com\s+Vicinal\s+\d{1,3}\b", score=0.95),
                Pattern(
                    name="quadra_lote",
                    regex=r"(?i)\b(?:quadra|qd\.?)\s*[A-Za-z0-9\-]+(?:\s*,?\s*(?:lote|lt\.?)\s*[A-Za-z0-9\-]+)?\b",
                    score=0.88,
                ),
                Pattern(
                    name="setor_condominio_residencial",
                    regex=r"(?i)\b(?:setor|condom[ií]nio|residencial)\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ0-9'`´.\-]+){0,5}\b",
                    score=0.82,
                ),
            ],
            supported_language="pt",
        )
    )
    if termos_estado_civil:
        analyzer.registry.add_recognizer(
            PatternRecognizer(
                supported_entity="ESTADO_CIVIL",
                name="EstadoCivilRecognizer",
                patterns=[Pattern(name=f"estado_civil_{t.lower()}", regex=rf"(?i)\b{re.escape(t)}\b", score=0.99) for t in termos_estado_civil],
                supported_language="pt",
            )
        )
    if termos_organizacoes_conhecidas:
        analyzer.registry.add_recognizer(
            PatternRecognizer(
                supported_entity="ORGANIZACAO_CONHECIDA",
                name="OrganizacaoConhecidaRecognizer",
                patterns=[Pattern(name=f"org_{t.lower()}", regex=rf"(?i)\b{re.escape(t)}\b", score=0.99) for t in termos_organizacoes_conhecidas],
                supported_language="pt",
            )
        )
    if termos_comuns_a_manter:
        recognizer_common_terms = PatternRecognizer(
            supported_entity="TERMO_COMUM",
            name="CommonTermsRecognizer",
            deny_list=termos_comuns_a_manter,
            supported_language="pt",
            deny_list_score=1.0,
        )
        analyzer.registry.add_recognizer(recognizer_common_terms)
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="CNH",
            name="CNHRecognizer",
            patterns=[Pattern(name="cnh_formatado", regex=r"\bCNH\s*(?:nº|n\.)?\s*\d{11}\b", score=0.99)],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="SIAPE",
            name="SIAPERecognizer",
            patterns=[
                Pattern(name="siape_formatado", regex=r"\bSIAPE\s*(?:nº|n\.)?\s*\d{7}\b", score=0.98),
                Pattern(name="siape_apenas_numeros", regex=r"\b(?<![\w])\d{7}(?![\w])\b", score=0.85),
            ],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="RG_NUMBER",
            name="CustomRgRecognizer",
            patterns=[
                Pattern(
                    name="rg_com_rotulo",
                    regex=r"(?i)\bRG\s*(?:n[ºo°.]?\s*)?[:\-]?\s*(?=[A-Z0-9.\-X]{3,20}\b)(?=[A-Z0-9.\-X]*\d)[A-Z0-9.\-X]{3,20}(?:\s*-\s*\dª\s*VIA)?(?:\s*[-,]?\s*(?:SSP|SESP|PC|IFP|DGPC|SJS|SJTC|SSDS|POL[ÍI]CIA\s+CIVIL)\s*\/\s*[A-Z]{2})?\b",
                    score=0.99,
                ),
                Pattern(
                    name="registro_geral_com_numero",
                    regex=r"(?i)\bRegistro\s+Geral\s*(?:n[ºo°.]?\s*)?[:\-]?\s*(?=[A-Z0-9.\-X]{3,20}\b)(?=[A-Z0-9.\-X]*\d)[A-Z0-9.\-X]{3,20}(?:\s*[-,]?\s*(?:SSP|SESP|PC|IFP|DGPC|SJS|SJTC|SSDS|POL[ÍI]CIA\s+CIVIL)\s*\/\s*[A-Z]{2})?\b",
                    score=0.98,
                ),
                Pattern(
                    name="cedula_ou_carteira_identidade_com_numero",
                    regex=r"(?i)\b(?:C[ÉE]DULA\s+DE\s+IDENTIDADE|CARTEIRA\s+DE\s+IDENTIDADE(?!\s+NACIONAL))\s*(?:n[ºo°.]?\s*)?[:\-]?\s*(?=[A-Z0-9.\-X]{3,20}\b)(?=[A-Z0-9.\-X]*\d)[A-Z0-9.\-X]{3,20}(?:\s*[-,]?\s*(?:SSP|SESP|PC|IFP|DGPC|SJS|SJTC|SSDS|POL[ÍI]CIA\s+CIVIL)\s*\/\s*[A-Z]{2})?\b",
                    score=0.95,
                ),
            ],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="MATRICULA_SIAPE",
            name="MatriculaSiapeRecognizer",
            patterns=[Pattern(name="matricula_siape", regex=r"(?i)\b(matr[íi]cula|siape)\b", score=0.95)],
            supported_language="pt",
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="ID_DOCUMENTO",
            name="IdDocumentoRecognizer",
            patterns=[
                Pattern(name="numero_beneficio_nb_formatado", regex=r"\bNB\s*\d{1,3}(\.?\d{3}){2}-[\dX]\b", score=0.98),
                Pattern(name="id_numerico_longo_pje", regex=r"\b\d{10,25}\b", score=0.97),
                Pattern(name="id_prefixo_numerico", regex=r"\bID\s*\d{8,12}\b", score=0.97),
                Pattern(name="numero_processo_cnj", regex=r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b", score=0.95),
                Pattern(name="numero_rnm", regex=r"\bRNM\s*(?:nº|n\.)?\s*[A-Z0-9]{7,15}\b", score=0.98),
                Pattern(name="numero_crm", regex=r"\bCRM\s*[A-Z]{2}\s*-\s*\d{1,6}\b", score=0.98),
            ],
            supported_language="pt",
        )
    )
    return analyzer


def carregar_anonymizer_engine():
    return AnonymizerEngine()

