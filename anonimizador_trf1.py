# Nome do arquivo: anonimizador_trf1.py
# Versão 0.90 - Interface de Download Corrigida 

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
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (opcional, mas bom manter)
load_dotenv()

# --- Constantes ---
NOME_ARQUIVO_SOBRENOMES = "sobrenomes_comuns.txt"
NOME_ARQUIVO_TERMOS_COMUNS = "termos_comuns.txt"

# --- Funções e Listas para o Motor de Anonimização ---
def carregar_lista_de_arquivo(nome_arquivo):
    lista_itens = []
    caminho_base = os.path.dirname(__file__)
    caminho_arquivo = os.path.join(caminho_base, nome_arquivo)
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                item = linha.strip()
                if item: lista_itens.append(item)
    except FileNotFoundError:
        print(f"AVISO: Arquivo de lista '{nome_arquivo}' não encontrado.")
    except Exception as e:
        print(f"ERRO: Erro ao ler o arquivo '{nome_arquivo}': {e}")
    return lista_itens

LISTA_SOBRENOMES_FREQUENTES_BR = carregar_lista_de_arquivo(NOME_ARQUIVO_SOBRENOMES)
LISTA_TERMOS_COMUNS = carregar_lista_de_arquivo(NOME_ARQUIVO_TERMOS_COMUNS)
LISTA_ESTADOS_CAPITAIS_BR = ["Acre","AC","Alagoas","AL","Amapá","AP","Amazonas","AM","Bahia","BA","Ceará","CE","Distrito Federal","DF","Espírito Santo","ES","Goiás","GO","Maranhão","MA","Mato Grosso","MT","Mato Grosso do Sul","MS","Minas Gerais","MG","Pará","PA","Paraíba","PB","Paraná","PR","Pernambuco","PE","Piauí","PI","Rio de Janeiro","RJ","Rio Grande do Norte","RN","Rio Grande do Sul","RS","Rondônia","RO","Roraima","RR","Santa Catarina","SC","São Paulo","SP","Sergipe","SE","Tocantins","TO","Aracaju","Belém","Belo Horizonte","Boa Vista","Brasília","Campo Grande","Cuiabá","Curitiba","Florianópolis","Fortaleza","Goiânia","João Pessoa","Macapá","Maceió","Manaus","Natal","Palmas","Porto Alegre","Porto Velho","Recife","Rio Branco","Salvador","São Luís","Teresina","Vitória"]
TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR = ["EXMO. SR. DR. JUIZ FEDERAL","EXMO SR DR JUIZ FEDERAL","EXCELENTÍSSIMO SENHOR DOUTOR JUIZ FEDERAL","JUIZ FEDERAL","EXMO. SR. DR. JUIZ DE DIREITO","EXMO SR DR JUIZ DE DIREITO","EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO","JUIZ DE DIREITO","JUIZADO ESPECIAL FEDERAL","VARA DA SEÇÃO JUDICIÁRIA","SEÇÃO JUDICIÁRIA","EXMO.","EXMO","SR.","DR.","Dra.","DRA.","EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) FEDERAL","EXCELENTÍSSIMO","Senhor","Doutor","Senhora","Doutora","EXCELENTÍSSIMA","EXCELENTÍSSIMO(A)","Senhor(a)","Doutor(a)","Juiz","Juíza","Juiz(a)","Juiz(íza)","Assunto","Assuntos"]
LISTA_ESTADO_CIVIL = ["casado","casada","solteiro","solteira","viúvo","viúva","divorciado","divorciada","separado","separada","unido","unida","companheiro","companheira","amasiado","amasiada","união estável","em união estável"]
LISTA_ORGANIZACOES_CONHECIDAS = ["FUNASA","INSS","IBAMA","CNPQ","IBGE","FIOCRUZ","SERPRO","DATAPREV","VALOR","Justiça","Justica","Segredo","PJe","Assunto","Tribunal Regional Federal","Assuntos","Vara Federal","Vara","Justiça Federal","Federal","Juizado","Especial","Federal","Vara Federal de Juizado Especial Cível","Turma","Turma Recursal","PJE","SJGO","SJDF","SJMA","SJAC","SJAL","SJAP","SJAM","SJBA","SJCE","SJDF","SJES","SJGO","SJMA","SJMG","SJMS","SJMT","SJPA","SJPB","SJPE","SJPI","SJPR","SJPE","SJRN","SJRO","SJRR","SJRS","SJSC","SJSE","SJSP","SJTO","Justiça Federal da 1ª Região","PJe - Processo Judicial Eletrônico", "Benefício", "Beneficio", "Benefícios", "Beneficios"]

# --- Configuração e Inicialização do Presidio (Motor Principal) ---
def carregar_analyzer_engine(termos_safe_location, termos_legal_header, lista_sobrenomes, termos_estado_civil, termos_organizacoes_conhecidas, termos_comuns_a_manter):
    try:
        spacy.load('pt_core_news_lg')
    except OSError:
        print("ERRO CRÍTICO: Modelo spaCy 'pt_core_news_lg' não encontrado. Instale com: python -m spacy download pt_core_news_lg")
        return None
    spacy_engine_obj = SpacyNlpEngine(models=[{'lang_code': 'pt', 'model_name': 'pt_core_news_lg'}])
    analyzer = AnalyzerEngine(nlp_engine=spacy_engine_obj, supported_languages=["pt"], default_score_threshold=0.4)
    if termos_safe_location: analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="SAFE_LOCATION", name="SafeLocationRecognizer", deny_list=termos_safe_location, supported_language="pt", deny_list_score=0.99))
    if termos_legal_header: analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="LEGAL_HEADER", name="LegalHeaderRecognizer", deny_list=termos_legal_header, supported_language="pt", deny_list_score=0.99))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CPF", name="CustomCpfRecognizer", patterns=[Pattern(name="CpfRegexPattern", regex=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", score=0.85)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="OAB_NUMBER", name="CustomOabRecognizer", patterns=[Pattern(name="OabRegexPattern", regex=r"\b(?:OAB\s+)?\d{1,6}(?:\.\d{3})?\s*\/\s*[A-Z]{2}\b", score=0.85)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CEP_NUMBER", name="CustomCepRecognizer", patterns=[Pattern(name="CepPattern", regex=r"\b(\d{5}-?\d{3}|\d{2}\.\d{3}-?\d{3})\b", score=0.80)], supported_language="pt"))
    if termos_estado_civil: analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="ESTADO_CIVIL", name="EstadoCivilRecognizer", patterns=[Pattern(name=f"estado_civil_{t.lower()}", regex=rf"(?i)\b{re.escape(t)}\b", score=0.99) for t in termos_estado_civil], supported_language="pt"))
    if termos_organizacoes_conhecidas: analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="ORGANIZACAO_CONHECIDA", name="OrganizacaoConhecidaRecognizer", patterns=[Pattern(name=f"org_{t.lower()}", regex=rf"(?i)\b{re.escape(t)}\b", score=0.99) for t in termos_organizacoes_conhecidas], supported_language="pt"))
    if lista_sobrenomes: analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="PERSON", name="BrazilianCommonSurnamesRecognizer", patterns=[Pattern(name=f"surname_{s.lower().replace(' ', '_')}", regex=rf"(?i)\b{re.escape(s)}\b", score=0.97) for s in lista_sobrenomes], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CNH", name="CNHRecognizer", patterns=[Pattern(name="cnh_formatado", regex=r"\bCNH\s*(?:nº|n\.)?\s*\d{11}\b", score=0.98), Pattern(name="cnh_apenas_numeros", regex=r"\b(?<![\w])\d{11}(?![\w])\b", score=0.85)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="SIAPE", name="SIAPERecognizer", patterns=[Pattern(name="siape_formatado", regex=r"\bSIAPE\s*(?:nº|n\.)?\s*\d{7}\b", score=0.98), Pattern(name="siape_apenas_numeros", regex=r"\b(?<![\w])\d{7}(?![\w])\b", score=0.85)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CI", name="CIRecognizer", patterns=[Pattern(name="ci_formatado", regex=r"\bCI\s*(?:nº|n\.)?\s*[\d.]{7,11}-?\d\b", score=0.98), Pattern(name="ci_padrao", regex=r"\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b", score=0.90)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="CIN", name="CINRecognizer", patterns=[Pattern(name="cin_formatado", regex=r"\bCIN\s*(?:nº|n\.)?\s*[\d.]{7,11}-?\d\b", score=0.98), Pattern(name="cin_padrao", regex=r"\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b", score=0.90)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="MATRICULA_SIAPE", name="MatriculaSiapeRecognizer", patterns=[Pattern(name="matricula_siape", regex=r"(?i)\b(matr[íi]cula|siape)\b", score=0.95)], supported_language="pt"))
    analyzer.registry.add_recognizer(PatternRecognizer(supported_entity="ID_DOCUMENTO", name="IdDocumentoRecognizer", patterns=[Pattern(name="numero_beneficio_nb_formatado", regex=r"\bNB\s*\d{1,3}(\.?\d{3}){2}-[\dX]\b", score=0.98), Pattern(name="id_numerico_longo_pje", regex=r"\b\d{10,25}\b", score=0.97), Pattern(name="id_prefixo_numerico", regex=r"\bID\s*\d{8,12}\b", score=0.97), Pattern(name="numero_rg_completo", regex=r"\bRG\s*(?:nº|n\.)?\s*[\d.X-]+(?:-\dª\s*VIA)?\s*-\s*[A-Z]{2,3}\/[A-Z]{2}\b", score=0.98), Pattern(name="numero_rg_simples", regex=r"\bRG\s*(?:nº|n\.)?\s*[\d.X-]+\b", score=0.97), Pattern(name="numero_processo_cnj", regex=r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b", score=0.95), Pattern(name="numero_rnm", regex=r"\bRNM\s*(?:nº|n\.)?\s*[A-Z0-9]{7,15}\b", score=0.98), Pattern(name="numero_crm", regex=r"\bCRM\s*[A-Z]{2}\s*-\s*\d{1,6}\b", score=0.98)], supported_language="pt"))
    return analyzer

def obter_operadores_anonimizacao():
    return {"DEFAULT": OperatorConfig("keep"),"PERSON": OperatorConfig("replace", {"new_value": "<NOME>"}),"LOCATION": OperatorConfig("replace", {"new_value": "<ENDERECO>"}),"EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),"PHONE_NUMBER": OperatorConfig("mask", {"type": "mask", "masking_char": "*", "chars_to_mask": 4, "from_end": True}),"CPF": OperatorConfig("replace", {"new_value": "<CPF>"}),"DATE_TIME": OperatorConfig("keep"),"OAB_NUMBER": OperatorConfig("replace", {"new_value": "<OAB>"}),"CEP_NUMBER": OperatorConfig("replace", {"new_value": "<CEP>"}),"ESTADO_CIVIL": OperatorConfig("keep"),"ORGANIZACAO_CONHECIDA": OperatorConfig("keep"),"ID_DOCUMENTO": OperatorConfig("keep"),"LEGAL_OR_COMMON_TERM": OperatorConfig("keep"),"CNH": OperatorConfig("replace", {"new_value": "***"}),"SIAPE": OperatorConfig("replace", {"new_value": "***"}),"CI": OperatorConfig("replace", {"new_value": "***"}),"CIN": OperatorConfig("replace", {"new_value": "***"}),"RG": OperatorConfig("replace", {"new_value": "***"}),"MATRICULA_SIAPE": OperatorConfig("replace", {"new_value": "***"})}

def carregar_anonymizer_engine(): return AnonymizerEngine()

analyzer_engine = carregar_analyzer_engine(LISTA_ESTADOS_CAPITAIS_BR, TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR, LISTA_SOBRENOMES_FREQUENTES_BR, LISTA_ESTADO_CIVIL, LISTA_ORGANIZACOES_CONHECIDAS, LISTA_TERMOS_COMUNS)
anonymizer_engine = carregar_anonymizer_engine()
operadores = obter_operadores_anonimizacao()

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
    entidades_para_analise = list(operadores.keys()) + ["SAFE_LOCATION", "LEGAL_HEADER", "ESTADO_CIVIL", "ORGANIZACAO_CONHECIDA", "ID_DOCUMENTO", "CNH", "SIAPE", "CI", "CIN", "MATRICULA_SIAPE"]
    entidades_para_analise = list(set(entidades_para_analise) - {"DEFAULT"})
    resultados_analise = analyzer_engine.analyze(text=texto_original, language='pt', entities=entidades_para_analise, return_decision_process=False)
    resultado_anonimizado_obj = anonymizer_engine.anonymize(text=texto_original, analyzer_results=resultados_analise, operators=operadores)
    
    dados_resultados = [{"Entidade": res.entity_type, "Texto Detectado": texto_original[res.start:res.end], "Início": res.start, "Fim": res.end, "Score": f"{res.score:.2f}"} for res in sorted(resultados_analise, key=lambda x: x.start)]
    return resultado_anonimizado_obj.text, pd.DataFrame(dados_resultados)

def processar_texto_area(texto_original):
    if not texto_original or not texto_original.strip():
        gr.Warning("Por favor, insira um texto na área para anonimizar.")
        return "O resultado da anonimização aparecerá aqui...", pd.DataFrame(None), None
    try:
        texto_anonimizado, df_resultados = _anonimizar_logica(texto_original)
        # <-- MUDANÇA: Gera o arquivo docx imediatamente
        caminho_arquivo_docx = gerar_arquivo_docx(texto_anonimizado)
        gr.Info("Texto da área anonimizado com sucesso!")
        # <-- MUDANÇA: Retorna também o caminho do arquivo
        return texto_anonimizado, df_resultados, caminho_arquivo_docx
    except Exception as e:
        gr.Error(f"Ocorreu um erro durante a anonimização: {e}")
        return "Erro ao processar o texto.", pd.DataFrame(None), None

def processar_arquivo_pdf(arquivo_temp, progress=gr.Progress()):
    if arquivo_temp is None:
        gr.Warning("Por favor, carregue um arquivo PDF.")
        return None, None, None
    
    progress(0, desc="Iniciando...")
    try:
        progress(0.2, desc="Extraindo texto do PDF...")
        texto_extraido, erro = extrair_texto_de_pdf(arquivo_temp.name)
        if erro:
            gr.Error(erro)
            return None, None, None

        progress(0.6, desc="Anonimizando o conteúdo...")
        texto_anonimizado, _ = _anonimizar_logica(texto_extraido)
        # <-- MUDANÇA: Gera o arquivo docx imediatamente
        caminho_arquivo_docx = gerar_arquivo_docx(texto_anonimizado)
        
        progress(1, desc="Concluído!")
        gr.Info("Arquivo PDF anonimizado com sucesso!")
        # <-- MUDANÇA: Retorna também o caminho do arquivo
        return texto_extraido, texto_anonimizado, caminho_arquivo_docx
    except Exception as e:
        gr.Error(f"Ocorreu um erro ao processar o PDF: {e}")
        return None, None, None

# --- CONSTRUÇÃO DA INTERFACE GRADIO SIMPLIFICADA ---
with gr.Blocks(theme=gr.themes.Soft(), title="Anonimizador TRF1") as demo:
    gr.Markdown("# ⚖️ Anonimizador TRF1\n**Ferramenta para anonimização de documentos com base no Microsoft Presidio.**")
    
    with gr.Tabs():
        with gr.TabItem("⌨️ Anonimizar Texto Colado"):
            with gr.Row():
                texto_original_area = gr.Textbox(lines=15, label="Texto Original", placeholder="Cole ou digite o texto aqui...")
                # <-- MUDANÇA: Agrupando a saída e o download em uma coluna
                with gr.Column():
                    texto_anonimizado_area = gr.Textbox(lines=14, label="Texto Anonimizado", interactive=False)
                    file_download_area = gr.File(label="Baixar como .docx", interactive=False)

            with gr.Row():
                btn_limpar_area = gr.Button("🗑️ Limpar")
                btn_anonimizar_area = gr.Button("🔍 Anonimizar Texto", variant="primary")
            
            with gr.Accordion("📊 Ver Entidades Detectadas", open=False):
                resultados_df_area = gr.DataFrame(label="Entidades Encontradas")

        with gr.TabItem("🗂️ Anonimizar Arquivo PDF"):
            gr.Markdown("### Passo 1: Carregue seu documento PDF")
            upload_pdf = gr.File(label="Selecione o arquivo PDF", file_types=['.pdf'])
            btn_anonimizar_pdf = gr.Button("🔍 Anonimizar PDF Carregado", variant="primary")
            
            gr.Markdown("### Passo 2: Confira os resultados")
            with gr.Row():
                with gr.Accordion("📄 Ver Texto Extraído do PDF (Original)", open=False):
                    texto_original_pdf = gr.Textbox(lines=15, label="Texto Original Extraído", interactive=False)
                
                # <-- MUDANÇA: Agrupando a saída e o download em uma coluna
                with gr.Column():
                    texto_anonimizado_pdf = gr.Textbox(lines=14, label="Texto Anonimizado", interactive=False)
                    file_download_pdf = gr.File(label="Baixar como .docx", interactive=False)

    # --- Lógica de Conexão dos Componentes (Event Listeners) ---
    # Aba de Texto
    # <-- MUDANÇA: O botão de anonimizar agora também atualiza o link de download
    btn_anonimizar_area.click(fn=processar_texto_area, inputs=[texto_original_area], outputs=[texto_anonimizado_area, resultados_df_area, file_download_area])
    btn_limpar_area.click(lambda: ("", "", pd.DataFrame(None), None), outputs=[texto_original_area, texto_anonimizado_area, resultados_df_area, file_download_area])
    
    # Aba de PDF
    # <-- MUDANÇA: O botão de anonimizar agora também atualiza o link de download
    btn_anonimizar_pdf.click(fn=processar_arquivo_pdf, inputs=[upload_pdf], outputs=[texto_original_pdf, texto_anonimizado_pdf, file_download_pdf])

# --- Ponto de Entrada para Iniciar o App ---
if __name__ == "__main__":
    if analyzer_engine and anonymizer_engine:
        print("Motores de anonimização carregados com sucesso. Iniciando a interface Gradio...")
        demo.launch()
    else:
        print("ERRO CRÍTICO: Não foi possível iniciar a aplicação pois os motores de anonimização falharam ao carregar.")