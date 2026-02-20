# Nome do arquivo: app.py (anonimizador_sinergia)
# Versão 0.96 - Versão Beta

import gradio as gr
import spacy
from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_analyzer.pattern import Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import pandas as pd
import io
import fitz  # PyMuPDF
from docx import Document
import re
import os
import time
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (opcional, mas bom manter)
load_dotenv()

# --- Constantes ---
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

# --- Funções e Listas para o Motor de Anonimização ---
def carregar_lista_de_arquivo(nome_arquivo):
    lista_itens = []
    caminho_base = os.path.dirname(__file__)
    caminho_arquivo = os.path.join(caminho_base, nome_arquivo)
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                item = linha.strip()
                if item:
                    lista_itens.append(item)
    except FileNotFoundError:
        print(f"AVISO: Arquivo de lista '{nome_arquivo}' não encontrado.")
    except Exception as e:
        print(f"ERRO: Erro ao ler o arquivo '{nome_arquivo}': {e}")
    return lista_itens


LISTA_SOBRENOMES_FREQUENTES_BR = carregar_lista_de_arquivo(NOME_ARQUIVO_SOBRENOMES)
LISTA_TERMOS_COMUNS = carregar_lista_de_arquivo(NOME_ARQUIVO_TERMOS_COMUNS)
LISTA_TITULOS_LEGAIS = carregar_lista_de_arquivo(NOME_ARQUIVO_TITULOS)
LISTA_ESTADOS_CAPITAIS_BR = ["Acre", "AC", "Alagoas", "AL", "Amapá", "AP", "Amazonas", "AM", "Bahia", "BA", "Ceará", "CE", "Distrito Federal", "DF", "Espírito Santo", "ES", "Goiás", "GO", "Maranhão", "MA", "Mato Grosso", "MT", "Mato Grosso do Sul", "MS", "Minas Gerais", "MG", "Pará", "PA", "Paraíba", "PB", "Paraná", "PR", "Pernambuco", "PE", "Piauí", "PI", "Rio de Janeiro", "RJ", "Rio Grande do Norte", "RN", "Rio Grande do Sul", "RS", "Rondônia", "RO", "Roraima", "RR", "Santa Catarina", "SC", "São Paulo", "SP", "Sergipe", "SE", "Tocantins", "TO",
                             "Aracaju", "Belém", "Belo Horizonte", "Boa Vista", "Brasília", "Campo Grande", "Cuiabá", "Curitiba", "Florianópolis", "Fortaleza", "Goiânia", "João Pessoa", "Macapá", "Maceió", "Manaus", "Natal", "Palmas", "Porto Alegre", "Porto Velho", "Recife", "Rio Branco", "Salvador", "São Luís", "Teresina", "Vitória"]
TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR = ["EXMO. SR. DR. JUIZ FEDERAL", "EXMO SR DR JUIZ FEDERAL", "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ FEDERAL", "JUIZ FEDERAL", "EXMO. SR. DR. JUIZ DE DIREITO", "EXMO SR DR JUIZ DE DIREITO", "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO", "JUIZ DE DIREITO", "JUIZADO ESPECIAL FEDERAL", "VARA DA SEÇÃO JUDICIÁRIA", "SEÇÃO JUDICIÁRIA", "EXMO.", "EXMO", "SR.", "DR.", "Dra.", "DRA.", "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) FEDERAL",
                                       "EXCELENTÍSSIMO", "Senhor", "Doutor", "Senhora", "Doutora", "EXCELENTÍSSIMA", "EXCELENTÍSSIMO(A)", "Senhor(a)", "Doutor(a)", "Juiz", "Juíza", "Juiz(a)", "Juiz(íza)", "Assunto", "Assuntos"]
LISTA_ESTADO_CIVIL = ["casado", "casada", "solteiro", "solteira", "viúvo", "viúva", "divorciado", "divorciada",
                      "separado", "separada", "unido", "unida", "companheiro", "companheira", "amasiado", "amasiada", "união estável", "em união estável"]
LISTA_ORGANIZACOES_CONHECIDAS = ["FUNASA", "INSS", "IBAMA", "CNPQ", "IBGE", "FIOCRUZ", "SERPRO", "DATAPREV", "VALOR", "Justiça", "Justica", "Segredo", "PJe", "Assunto", "Tribunal Regional Federal", "Assuntos", "Vara Federal", "Vara", "Justiça Federal", "Federal", "Juizado", "Especial", "Federal", "Vara Federal de Juizado Especial Cível", "Turma",
                                "Turma Recursal", "PJE", "SJGO", "SJDF", "SJMA", "SJAC", "SJAL", "SJAP", "SJAM", "SJBA", "SJCE", "SJDF", "SJES", "SJGO", "SJMA", "SJMG", "SJMS", "SJMT", "SJPA", "SJPB", "SJPE", "SJPI", "SJPR", "SJPE", "SJRN", "SJRO", "SJRR", "SJRS", "SJSC", "SJSE", "SJSP", "SJTO", "Justiça Federal da 1ª Região", "PJe - Processo Judicial Eletrônico"]

# --- Configuração e Inicialização do Presidio (Motor Principal) ---
def carregar_analyzer_engine(termos_safe_location, termos_legal_header, lista_sobrenomes, termos_estado_civil, termos_organizacoes_conhecidas, termos_comuns_a_manter, titulos_legais):
    try:
        spacy.load('pt_core_news_lg')
    except OSError:
        print("ERRO CRÍTICO: Modelo spaCy 'pt_core_news_lg' não encontrado. Instale com: python -m spacy download pt_core_news_lg")
        return None
    spacy_engine_obj = SpacyNlpEngine(
        models=[{'lang_code': 'pt', 'model_name': 'pt_core_news_lg'}])
    analyzer = AnalyzerEngine(
        nlp_engine=spacy_engine_obj, supported_languages=["pt"], default_score_threshold=0.4)
    if termos_safe_location:
        analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="SAFE_LOCATION", name="SafeLocationRecognizer",
                                                            deny_list=termos_safe_location, supported_language="pt", deny_list_score=0.99))
    if termos_legal_header:
        analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="LEGAL_HEADER", name="LegalHeaderRecognizer",
                                                            deny_list=termos_legal_header, supported_language="pt", deny_list_score=0.99))

    if titulos_legais:
        palavras_para_regex = '|'.join(titulos_legais)
        legal_titles_pattern = Pattern(
            name="legal_title_pattern",
            regex=rf"(?i)\b({palavras_para_regex})(?:\([A-Z]\))?\b",
            score=1.0
        )
        legal_title_recognizer = PatternRecognizer(
            supported_entity="LEGAL_TITLE",
            name="LegalTitleRecognizer",
            patterns=[legal_titles_pattern],
            supported_language="pt"
        )
        analyzer.registry.add_recognizer(legal_title_recognizer)

    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CPF", name="CustomCpfRecognizer", patterns=[
        Pattern(name="CpfRegexPattern", regex=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", score=0.85)
    ], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="OAB_NUMBER", name="CustomOabRecognizer", patterns=[
                                      Pattern(name="OabRegexPattern", regex=r"\b(?:OAB\s+)?\d{1,6}(?:\.\d{3})?\s*\/\s*[A-Z]{2}\b", score=0.85)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CEP_NUMBER", name="CustomCepRecognizer", patterns=[
                                      Pattern(name="CepPattern", regex=r"\b(\d{5}-?\d{3}|\d{2}\.\d{3}-?\d{3})\b", score=0.80)], supported_language="pt"))
    if termos_estado_civil:
        analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="ESTADO_CIVIL", name="EstadoCivilRecognizer", patterns=[
                                      Pattern(name=f"estado_civil_{t.lower()}", regex=rf"(?i)\b{re.escape(t)}\b", score=0.99) for t in termos_estado_civil], supported_language="pt"))
    if termos_organizacoes_conhecidas:
        analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="ORGANIZACAO_CONHECIDA", name="OrganizacaoConhecidaRecognizer", patterns=[
                                      Pattern(name=f"org_{t.lower()}", regex=rf"(?i)\b{re.escape(t)}\b", score=0.99) for t in termos_organizacoes_conhecidas], supported_language="pt"))
    if termos_comuns_a_manter:
        recognizer_common_terms = PatternRecognizer(
            supported_entity="TERMO_COMUM", name="CommonTermsRecognizer", deny_list=termos_comuns_a_manter, supported_language="pt", deny_list_score=1.0)
        analyzer.registry.add_recognizer(recognizer_common_terms)
    if lista_sobrenomes:
        analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="PERSON", name="BrazilianCommonSurnamesRecognizer", patterns=[
                                      Pattern(name=f"surname_{s.lower().replace(' ', '_')}", regex=rf"(?i)\b{re.escape(s)}\b", score=0.97) for s in lista_sobrenomes], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CNH", name="CNHRecognizer", patterns=[
        Pattern(name="cnh_formatado", regex=r"\bCNH\s*(?:nº|n\.)?\s*\d{11}\b", score=0.99),
        Pattern(name="cnh_apenas_numeros", regex=r"\b(?<![\w])\d{11}(?![\w])\b", score=0.98)
    ], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="SIAPE", name="SIAPERecognizer", patterns=[Pattern(
        name="siape_formatado", regex=r"\bSIAPE\s*(?:nº|n\.)?\s*\d{7}\b", score=0.98), Pattern(name="siape_apenas_numeros", regex=r"\b(?<![\w])\d{7}(?![\w])\b", score=0.85)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CI", name="CIRecognizer", patterns=[Pattern(name="ci_formatado", regex=r"\bCI\s*(?:nº|n\.)?\s*[\d.]{7,11}-?\d\b", score=0.98), Pattern(
        name="ci_padrao", regex=r"\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b", score=0.90)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CIN", name="CINRecognizer", patterns=[Pattern(name="cin_formatado", regex=r"\bCIN\s*(?:nº|n\.)?\s*[\d.]{7,11}-?\d\b", score=0.98), Pattern(
        name="cin_padrao", regex=r"\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b", score=0.90)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="RG_NUMBER",
        name="CustomRgRecognizer",
        patterns=[
            Pattern(name="numero_rg_completo", regex=r"\bRG\s*(?:nº|n\.)?\s*[\d.X-]+(?:-\dª\s*VIA)?\s*-\s*[A-Z]{2,3}\/[A-Z]{2}\b", score=0.99),
            Pattern(name="numero_rg_simples", regex=r"\bRG\s*(?:nº|n\.)?\s*[\d.X-]+\b", score=0.98)
        ],
        supported_language="pt"
    ))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="MATRICULA_SIAPE", name="MatriculaSiapeRecognizer", patterns=[
                                      Pattern(name="matricula_siape", regex=r"(?i)\b(matr[íi]cula|siape)\b", score=0.95)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="TERMO_IDENTIDADE", name="TermoIdentidadeRecognizer", patterns=[
                                      Pattern(name="termo_rg_id", regex=r"(?i)\b(RG|carteira|identidade|ssp)\b", score=0.95)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="ID_DOCUMENTO", name="IdDocumentoRecognizer", patterns=[
        Pattern(name="numero_beneficio_nb_formatado", regex=r"\bNB\s*\d{1,3}(\.?\d{3}){2}-[\dX]\b", score=0.98),
        Pattern(name="id_numerico_longo_pje", regex=r"\b\d{10,25}\b", score=0.97),
        Pattern(name="id_prefixo_numerico", regex=r"\bID\s*\d{8,12}\b", score=0.97),
        Pattern(name="numero_processo_cnj", regex=r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b", score=0.95),
        Pattern(name="numero_rnm", regex=r"\bRNM\s*(?:nº|n\.)?\s*[A-Z0-9]{7,15}\b", score=0.98),
        Pattern(name="numero_crm", regex=r"\bCRM\s*[A-Z]{2}\s*-\s*\d{1,6}\b", score=0.98)
    ], supported_language="pt"))
    return analyzer


def obter_operadores_anonimizacao():
    return {
        "DEFAULT": OperatorConfig("keep"),
        "PERSON": OperatorConfig("replace", {"new_value": "<NOME>"}),
        "LOCATION": OperatorConfig("replace", {"new_value": "<ENDERECO>"}),
        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
        "PHONE_NUMBER": OperatorConfig("mask", {"type": "mask", "masking_char": "*", "chars_to_mask": 4, "from_end": True}),
        "CPF": OperatorConfig("replace", {"new_value": "<CPF>"}),
        "DATE_TIME": OperatorConfig("keep"),
        "OAB_NUMBER": OperatorConfig("replace", {"new_value": "<OAB>"}),
        "CEP_NUMBER": OperatorConfig("replace", {"new_value": "<CEP>"}),
        "ESTADO_CIVIL": OperatorConfig("keep"),
        "ORGANIZACAO_CONHECIDA": OperatorConfig("keep"),
        "ID_DOCUMENTO": OperatorConfig("keep"),
        "LEGAL_TITLE": OperatorConfig("keep"), # <-- CORREÇÃO 2: REGRA ADICIONADA
        "LEGAL_OR_COMMON_TERM": OperatorConfig("keep"),
        "CNH": OperatorConfig("replace", {"new_value": "***********"}),
        "SIAPE": OperatorConfig("replace", {"new_value": "***"}),
        "CI": OperatorConfig("replace", {"new_value": "***"}),
        "CIN": OperatorConfig("replace", {"new_value": "***"}),
        "RG_NUMBER": OperatorConfig("replace", {"new_value": "<NUMERO RG>"}),
        "RG": OperatorConfig("replace", {"new_value": "***"}),
        "MATRICULA_SIAPE": OperatorConfig("replace", {"new_value": "***"}),
        "TERMO_IDENTIDADE": OperatorConfig("replace", {"new_value": "***"}),
        "TERMO_COMUM": OperatorConfig("keep")
    }

def carregar_anonymizer_engine(): return AnonymizerEngine()


# ---> CORREÇÃO 1: INICIALIZAÇÃO CORRIGIDA <---
analyzer_engine = carregar_analyzer_engine(
    LISTA_ESTADOS_CAPITAIS_BR,
    TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR,
    LISTA_SOBRENOMES_FREQUENTES_BR,
    LISTA_ESTADO_CIVIL,
    LISTA_ORGANIZACOES_CONHECIDAS,
    LISTA_TERMOS_COMUNS,
    LISTA_TITULOS_LEGAIS
)
anonymizer_engine = carregar_anonymizer_engine() # Corrigido de 'carregar_analyzer_engine'
operadores = obter_operadores_anonimizacao()

def dataframe_entidades_vazio():
    return pd.DataFrame(columns=COLUNAS_ENTIDADES_DETECTADAS)


def gerar_resumo_processamento(df_resultados, origem, tempo_segundos=None):
    sufixo_tempo = ""
    if tempo_segundos is not None:
        sufixo_tempo = f" Tempo total: {tempo_segundos:.2f}s."
    if df_resultados is None or df_resultados.empty:
        return f"**Resumo ({origem}):** nenhuma entidade detectada.{sufixo_tempo}"
    total_entidades = len(df_resultados)
    tipos_unicos = df_resultados["Entidade"].nunique()
    top_tipos = df_resultados["Entidade"].value_counts().head(3)
    top_formatado = ", ".join([f"{entidade} ({qtde})" for entidade, qtde in top_tipos.items()])
    return (
        f"**Resumo ({origem}):** {total_entidades} entidades detectadas em "
        f"{tipos_unicos} tipos. Principais ocorrencias: {top_formatado}.{sufixo_tempo}"
    )

def extrair_texto_de_pdf(caminho_arquivo_pdf):
    texto_completo = ""
    try:
        with fitz.open(caminho_arquivo_pdf) as documento_pdf:
            for pagina in documento_pdf:
                texto_completo += pagina.get_text()
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}")
        return None, f"Erro ao extrair texto do PDF: {e}"
    if not texto_completo.strip():
        return None, "O PDF carregado não contém texto extraível."
    return texto_completo, None


def gerar_arquivo_docx(texto):
    if not texto or texto.strip() == "":
        return None
    try:
        documento = Document()
        documento.add_paragraph(texto)
        filepath = "documento_anonimizado.docx"
        documento.save(filepath)
        return filepath
    except Exception as e:
        gr.Error(f"Erro ao gerar o arquivo .docx: {e}")
        return None


# --- Funções de Lógica da Interface (Event Handlers) ---
def _anonimizar_logica(texto_original):
    entidades_para_analise = list(operadores.keys()) + ["SAFE_LOCATION", "LEGAL_HEADER", "ESTADO_CIVIL",
                                                        "ORGANIZACAO_CONHECIDA", "ID_DOCUMENTO", "CNH", "SIAPE", "CI", "CIN", "MATRICULA_SIAPE"]
    entidades_para_analise = list(set(entidades_para_analise) - {"DEFAULT"})
    resultados_analise = analyzer_engine.analyze(
        text=texto_original, language='pt', entities=entidades_para_analise, return_decision_process=False)
    resultado_anonimizado_obj = anonymizer_engine.anonymize(
        text=texto_original, analyzer_results=resultados_analise, operators=operadores)
    dados_resultados = [{"Entidade": res.entity_type, "Texto Detectado": texto_original[res.start:res.end], "Início": res.start,
                         "Fim": res.end, "Score": f"{res.score:.2f}"} for res in sorted(resultados_analise, key=lambda x: x.start)]
    return resultado_anonimizado_obj.text, pd.DataFrame(dados_resultados)


def atualizar_estado_botao_texto(texto_original):
    texto_valido = bool(texto_original and texto_original.strip())
    return gr.update(interactive=texto_valido)


def atualizar_estado_botao_pdf(arquivo_temp):
    return gr.update(interactive=arquivo_temp is not None)


def desativar_botao():
    return gr.update(interactive=False)


def processar_texto_area(texto_original):
    if not texto_original or not texto_original.strip():
        gr.Warning("Cole ou digite um texto antes de iniciar a anonimização.")
        return ESTADO_VAZIO_TEXTO_ANONIMIZADO, dataframe_entidades_vazio(), RESUMO_VAZIO_TEXTO
    inicio_processamento = time.perf_counter()
    try:
        texto_anonimizado, df_resultados = _anonimizar_logica(texto_original)
        tempo_total = time.perf_counter() - inicio_processamento
        resumo_processamento = gerar_resumo_processamento(df_resultados, "Texto", tempo_total)
        gr.Info("Texto da área anonimizado com sucesso!")
        return texto_anonimizado, df_resultados, resumo_processamento
    except Exception as e:
        gr.Error(f"Ocorreu um erro durante a anonimização: {e}")
        tempo_total = time.perf_counter() - inicio_processamento
        return "Não foi possível processar o texto.", dataframe_entidades_vazio(), f"**Resumo:** erro no processamento. Tempo total: {tempo_total:.2f}s."


def limpar_texto_area():
    return "", ESTADO_VAZIO_TEXTO_ANONIMIZADO, dataframe_entidades_vazio(), RESUMO_VAZIO_TEXTO, gr.update(interactive=False)


def processar_arquivo_pdf(arquivo_temp, progress=gr.Progress()):
    if arquivo_temp is None:
        gr.Warning("Selecione um arquivo PDF antes de iniciar a anonimização.")
        return ESTADO_VAZIO_PDF_ORIGINAL, ESTADO_VAZIO_PDF_ANONIMIZADO, RESUMO_VAZIO_PDF
    inicio_processamento = time.perf_counter()
    progress(0, desc="Iniciando...")
    try:
        progress(0.2, desc="Extraindo texto do PDF...")
        texto_extraido, erro = extrair_texto_de_pdf(arquivo_temp.name)
        if erro:
            gr.Error(erro)
            tempo_total = time.perf_counter() - inicio_processamento
            return ESTADO_VAZIO_PDF_ORIGINAL, ESTADO_VAZIO_PDF_ANONIMIZADO, f"**Resumo:** erro na extração. Tempo total: {tempo_total:.2f}s."
        progress(0.6, desc="Anonimizando o conteúdo...")
        texto_anonimizado, df_resultados = _anonimizar_logica(texto_extraido)
        tempo_total = time.perf_counter() - inicio_processamento
        resumo_processamento = gerar_resumo_processamento(df_resultados, "PDF", tempo_total)
        progress(1, desc="Concluído!")
        gr.Info("Arquivo PDF anonimizado com sucesso!")
        return texto_extraido, texto_anonimizado, resumo_processamento
    except Exception as e:
        gr.Error(f"Ocorreu um erro ao processar o PDF: {e}")
        tempo_total = time.perf_counter() - inicio_processamento
        return ESTADO_VAZIO_PDF_ORIGINAL, ESTADO_VAZIO_PDF_ANONIMIZADO, f"**Resumo:** erro no processamento. Tempo total: {tempo_total:.2f}s."

# --- CSS Customizado para aumentar o botão de cópia ---
custom_css = """
:root {
    --font-base: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    --color-primary: #0b5cab;
    --color-primary-hover: #084987;
    --color-bg-subtle: #f5f8fc;
    --color-border: #d8e0eb;
    --space-1: 8px;
    --space-2: 16px;
    --space-3: 24px;
    --radius-1: 10px;
}

.gradio-container {
    font-family: var(--font-base);
    padding: var(--space-3) !important;
}

#header {
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-2);
}

#header h1 {
    margin-bottom: var(--space-1) !important;
}

.gradio-container .tabs {
    margin-top: var(--space-2);
}

.gradio-container .tabitem {
    padding-top: var(--space-2);
}

.gradio-container .gr-accordion {
    margin-top: var(--space-2);
}

.gradio-container textarea,
.gradio-container input[type="text"],
.gradio-container input[type="file"],
.gradio-container table {
    border-radius: var(--radius-1) !important;
    border-color: var(--color-border) !important;
}

.gradio-container .gr-button {
    border-radius: var(--radius-1) !important;
    padding: var(--space-1) var(--space-2) !important;
}

.gradio-container .gr-button.primary {
    background: var(--color-primary) !important;
    border-color: var(--color-primary) !important;
}

.gradio-container .gr-button.primary:hover {
    background: var(--color-primary-hover) !important;
    border-color: var(--color-primary-hover) !important;
}

.gradio-container .gr-button:not(.primary) {
    background: #f2f4f7 !important;
    color: #1f2937 !important;
    border-color: #cfd8e3 !important;
}

.gradio-container .gr-button:not(.primary):hover {
    background: #e7edf4 !important;
    border-color: #b8c4d1 !important;
}

.gradio-container .cta-row {
    gap: var(--space-1);
    margin-bottom: var(--space-1);
}

.gradio-container .gr-markdown {
    margin-bottom: var(--space-2);
}

.gradio-container > .gr-markdown:nth-of-type(2) {
    background: var(--color-bg-subtle);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-1);
    padding: var(--space-2);
}

button.copy-button {
    padding: 6px !important;
    min-width: 36px !important;
    min-height: 36px !important;
}

button.copy-button > svg {
    transform: scale(1.1);
}
"""

# --- CONSTRUÇÃO DA INTERFACE GRADIO ---
with gr.Blocks(theme=gr.themes.Soft(), title="Anonimizador TRF1", css=custom_css) as demo:

    with gr.Row(elem_id="header"):
        with gr.Column(scale=0, min_width=120):
            gr.Image(value=LOGO_FILE_PATH, interactive=False,
                     show_download_button=False, show_label=False, width=100)
        with gr.Column(scale=4):
            gr.Markdown(
                """
                # Anonimizador SINERGIA
                **Anonimize textos jurídicos com apoio de NLP e regras customizadas.**
                Desenvolvido pelo Projeto Sinergia - TRF1.
                """
            )

    gr.Markdown(
        """
        ### Limites e privacidade
        - Esta ferramenta processa o texto enviado para detectar e anonimizar entidades.
        - PDFs digitalizados como imagem podem não conter texto extraível (OCR não incluso nesta versão).
        - Revise o resultado antes de compartilhar o documento, pois nenhum modelo acerta 100% dos casos.
        - Siga as políticas internas de privacidade e LGPD ao usar dados pessoais.
        """
    )

    with gr.Tabs():
        with gr.TabItem("Anonimizar texto"):
            gr.Markdown("### Passo 1: cole o texto original e clique em **Anonimizar texto**.")
            with gr.Row():
                with gr.Column(scale=1):
                    texto_original_area = gr.Textbox(
                        lines=15,
                        label="Texto original",
                        placeholder="Cole ou digite o conteúdo que deseja anonimizar.")

                with gr.Column(scale=1):
                    texto_anonimizado_area = gr.Textbox(
                        lines=15,
                        value=ESTADO_VAZIO_TEXTO_ANONIMIZADO,
                        label="Texto anonimizado",
                        interactive=False,
                        show_copy_button=True)

            with gr.Row(elem_classes=["cta-row"]):
                btn_anonimizar_area = gr.Button("Anonimizar texto", variant="primary", size="lg", interactive=False)
                btn_limpar_area = gr.Button("Limpar campos", variant="secondary")
            resumo_texto_area = gr.Markdown(value=RESUMO_VAZIO_TEXTO)

            with gr.Accordion("Ver entidades detectadas", open=False):
                resultados_df_area = gr.DataFrame(
                    label="Entidades encontradas",
                    value=dataframe_entidades_vazio(),
                    interactive=False)

        with gr.TabItem("Anonimizar arquivo PDF"):
            gr.Markdown("### Passo 1: envie um PDF com texto pesquisável e clique em **Anonimizar PDF**.")
            upload_pdf = gr.File(label="Selecione o arquivo PDF", file_types=['.pdf'])
            with gr.Row(elem_classes=["cta-row"]):
                btn_anonimizar_pdf = gr.Button("Anonimizar PDF", variant="primary", size="lg", interactive=False)
            resumo_pdf = gr.Markdown(value=RESUMO_VAZIO_PDF)
            gr.Markdown("### Passo 2: revise o texto original extraído e a versão anonimizada.")
            with gr.Row():
                with gr.Accordion("Ver texto original extraído do PDF", open=False):
                    texto_original_pdf = gr.Textbox(
                        lines=15,
                        value=ESTADO_VAZIO_PDF_ORIGINAL,
                        label="Texto original extraído",
                        interactive=False)
                with gr.Column():
                    texto_anonimizado_pdf = gr.Textbox(
                        lines=14,
                        value=ESTADO_VAZIO_PDF_ANONIMIZADO,
                        label="Texto anonimizado",
                        interactive=False,
                        show_copy_button=True)

    # --- Lógica de Conexão dos Componentes (Event Listeners) ---
    texto_original_area.change(fn=atualizar_estado_botao_texto, inputs=[texto_original_area], outputs=[btn_anonimizar_area])
    upload_pdf.change(fn=atualizar_estado_botao_pdf, inputs=[upload_pdf], outputs=[btn_anonimizar_pdf])
    evento_anonimizar_texto = btn_anonimizar_area.click(
        fn=desativar_botao,
        outputs=[btn_anonimizar_area],
        queue=False,
    ).then(
        fn=processar_texto_area,
        inputs=[texto_original_area],
        outputs=[texto_anonimizado_area, resultados_df_area, resumo_texto_area],
    )
    evento_anonimizar_texto.then(
        fn=atualizar_estado_botao_texto,
        inputs=[texto_original_area],
        outputs=[btn_anonimizar_area],
        queue=False,
    )
    btn_limpar_area.click(fn=limpar_texto_area, outputs=[
                          texto_original_area, texto_anonimizado_area, resultados_df_area, resumo_texto_area, btn_anonimizar_area])
    evento_anonimizar_pdf = btn_anonimizar_pdf.click(
        fn=desativar_botao,
        outputs=[btn_anonimizar_pdf],
        queue=False,
    ).then(
        fn=processar_arquivo_pdf,
        inputs=[upload_pdf],
        outputs=[texto_original_pdf, texto_anonimizado_pdf, resumo_pdf],
    )
    evento_anonimizar_pdf.then(
        fn=atualizar_estado_botao_pdf,
        inputs=[upload_pdf],
        outputs=[btn_anonimizar_pdf],
        queue=False,
    )

# --- Ponto de Entrada para Iniciar o App ---
if __name__ == "__main__":
    if analyzer_engine and anonymizer_engine:
        print("Motores de anonimização carregados com sucesso. Iniciando a interface Gradio...")
        demo.launch()
    else:
        print("ERRO CRÍTICO: Não foi possível iniciar a aplicação pois os motores de anonimização falharam ao carregar.")
