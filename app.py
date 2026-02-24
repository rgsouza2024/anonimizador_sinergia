# Nome do arquivo: app.py (anonimizador_sinergia)
# Versão 0.96 - Versão Beta

import gradio as gr
from dotenv import load_dotenv
from core.config import (
    COLUNAS_ENTIDADES_DETECTADAS,
    ESTADO_VAZIO_PDF_ANONIMIZADO,
    ESTADO_VAZIO_PDF_ORIGINAL,
    ESTADO_VAZIO_TEXTO_ANONIMIZADO,
    LOGO_FILE_PATH,
    PLACEHOLDER_NOME_PARTE_INTERNO,
    RESUMO_VAZIO_PDF,
    RESUMO_VAZIO_TEXTO,
)
from core.operators import obter_operadores_anonimizacao
from core.app_services import (
    dataframe_entidades_vazio as service_dataframe_entidades_vazio,
    extrair_texto_de_pdf as service_extrair_texto_de_pdf,
    gerar_resumo_processamento as service_gerar_resumo_processamento,
)
from core.engine_setup import carregar_analyzer_engine, carregar_anonymizer_engine
from core.pipeline import executar_pipeline_anonimizacao
from core.resources import (
    LISTA_ESTADO_CIVIL,
    LISTA_ESTADOS_CAPITAIS_BR,
    LISTA_NOMES_COMUNS,
    LISTA_ORGANIZACOES_CONHECIDAS,
    LISTA_TERMOS_COMUNS,
    LISTA_TITULOS_LEGAIS,
    TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR,
)
from core.text_filters import (
    anonimizar_nomes_pf_metadados,
    anonimizar_por_lista_nomes_comuns,
    anonimizar_nomes_extraidos,
    extrair_nomes_parte_alvo,
    extrair_nomes_pessoais_contextuais,
    filtrar_resultados_analise,
    normalizar_placeholders_nome_parte,
)
from core.interface_builder import criar_interface_gradio
from core.ui_handlers import (
    atualizar_estado_botao_pdf as ui_atualizar_estado_botao_pdf,
    atualizar_estado_botao_texto as ui_atualizar_estado_botao_texto,
    desativar_botao as ui_desativar_botao,
    limpar_texto_area as ui_limpar_texto_area,
    processar_arquivo_pdf as ui_processar_arquivo_pdf,
    processar_texto_area as ui_processar_texto_area,
)

# Carrega as variáveis de ambiente do arquivo .env (opcional, mas bom manter)
load_dotenv()

# --- Funções e Listas para o Motor de Anonimização ---
# --- Configuração e Inicialização do Presidio (Motor Principal) ---
analyzer_engine = carregar_analyzer_engine(
    LISTA_ESTADOS_CAPITAIS_BR,
    TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR,
    LISTA_NOMES_COMUNS,
    LISTA_ESTADO_CIVIL,
    LISTA_ORGANIZACOES_CONHECIDAS,
    LISTA_TERMOS_COMUNS,
    LISTA_TITULOS_LEGAIS
)
anonymizer_engine = carregar_anonymizer_engine()
operadores = obter_operadores_anonimizacao()

def dataframe_entidades_vazio():
    return service_dataframe_entidades_vazio(COLUNAS_ENTIDADES_DETECTADAS)


def gerar_resumo_processamento(df_resultados, origem, tempo_segundos=None, info_metadado_pdf=None):
    return service_gerar_resumo_processamento(df_resultados, origem, tempo_segundos, info_metadado_pdf)

def extrair_texto_de_pdf(caminho_arquivo_pdf):
    return service_extrair_texto_de_pdf(caminho_arquivo_pdf)

# --- Funções de Lógica da Interface (Event Handlers) ---
def _anonimizar_logica(texto_original, nomes_pf_metadados=None, retornar_metricas=False):
    return executar_pipeline_anonimizacao(
        texto_original=texto_original,
        analyzer_engine=analyzer_engine,
        anonymizer_engine=anonymizer_engine,
        operadores=operadores,
        anonimizar_nomes_pf_metadados_fn=anonimizar_nomes_pf_metadados,
        nomes_pf_metadados=nomes_pf_metadados or set(),
        extrair_nomes_parte_alvo_fn=extrair_nomes_parte_alvo,
        extrair_nomes_pessoais_contextuais_fn=extrair_nomes_pessoais_contextuais,
        anonimizar_nomes_extraidos_fn=anonimizar_nomes_extraidos,
        anonimizar_por_lista_nomes_comuns_fn=anonimizar_por_lista_nomes_comuns,
        lista_nomes_comuns=LISTA_NOMES_COMUNS,
        filtrar_resultados_analise_fn=filtrar_resultados_analise,
        normalizar_placeholders_nome_parte_fn=normalizar_placeholders_nome_parte,
        placeholder_nome_parte_interno=PLACEHOLDER_NOME_PARTE_INTERNO,
        retornar_metricas=retornar_metricas,
    )

def atualizar_estado_botao_texto(texto_original):
    return ui_atualizar_estado_botao_texto(texto_original)


def atualizar_estado_botao_pdf(arquivo_temp):
    return ui_atualizar_estado_botao_pdf(arquivo_temp)


def desativar_botao():
    return ui_desativar_botao()


def processar_texto_area(texto_original):
    return ui_processar_texto_area(
        texto_original=texto_original,
        anonimizar_logica_fn=_anonimizar_logica,
        dataframe_entidades_vazio_fn=dataframe_entidades_vazio,
        gerar_resumo_processamento_fn=gerar_resumo_processamento,
        estado_vazio_texto_anonimizado=ESTADO_VAZIO_TEXTO_ANONIMIZADO,
        resumo_vazio_texto=RESUMO_VAZIO_TEXTO,
    )


def limpar_texto_area():
    return ui_limpar_texto_area(
        dataframe_entidades_vazio_fn=dataframe_entidades_vazio,
        estado_vazio_texto_anonimizado=ESTADO_VAZIO_TEXTO_ANONIMIZADO,
        resumo_vazio_texto=RESUMO_VAZIO_TEXTO,
    )


def processar_arquivo_pdf(arquivo_temp, progress=gr.Progress()):
    return ui_processar_arquivo_pdf(
        arquivo_temp=arquivo_temp,
        anonimizar_logica_fn=_anonimizar_logica,
        extrair_texto_de_pdf_fn=extrair_texto_de_pdf,
        gerar_resumo_processamento_fn=gerar_resumo_processamento,
        estado_vazio_pdf_original=ESTADO_VAZIO_PDF_ORIGINAL,
        estado_vazio_pdf_anonimizado=ESTADO_VAZIO_PDF_ANONIMIZADO,
        resumo_vazio_pdf=RESUMO_VAZIO_PDF,
        progress=progress,
    )

demo = criar_interface_gradio(
    logo_file_path=LOGO_FILE_PATH,
    estado_vazio_texto_anonimizado=ESTADO_VAZIO_TEXTO_ANONIMIZADO,
    estado_vazio_pdf_original=ESTADO_VAZIO_PDF_ORIGINAL,
    estado_vazio_pdf_anonimizado=ESTADO_VAZIO_PDF_ANONIMIZADO,
    resumo_vazio_texto=RESUMO_VAZIO_TEXTO,
    resumo_vazio_pdf=RESUMO_VAZIO_PDF,
    dataframe_entidades_vazio_fn=dataframe_entidades_vazio,
    atualizar_estado_botao_texto_fn=atualizar_estado_botao_texto,
    atualizar_estado_botao_pdf_fn=atualizar_estado_botao_pdf,
    desativar_botao_fn=desativar_botao,
    processar_texto_area_fn=processar_texto_area,
    limpar_texto_area_fn=limpar_texto_area,
    processar_arquivo_pdf_fn=processar_arquivo_pdf,
)

# --- Ponto de Entrada para Iniciar o App ---
if __name__ == "__main__":
    if analyzer_engine and anonymizer_engine:
        print("Motores de anonimização carregados com sucesso. Iniciando a interface Gradio...")
        demo.launch()
    else:
        print("ERRO CRÍTICO: Não foi possível iniciar a aplicação pois os motores de anonimização falharam ao carregar.")
