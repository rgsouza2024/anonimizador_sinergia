"""Serviço central do motor de anonimização (sem dependência de interfaces gráficas)."""

from core.config import PLACEHOLDER_NOME_PARTE_INTERNO
from core.operators import obter_operadores_anonimizacao
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
    aplicar_lista_nomes_comuns,
    aplicar_nomes_extraidos,
    aplicar_nomes_pf_metadados,
    aplicar_sobrenomes_raros,
    extrair_nomes_parte_alvo,
    extrair_nomes_papel_penal,
    extrair_nomes_pessoais_contextuais,
    filtrar_resultados_analise,
    normalizar_placeholders_nome_parte,
    spans_agentes_publicos,
    spans_nao_tarjar,
    spans_nomes_manuais,
)

# Inicialização única dos motores de NLP e analisadores
analyzer_engine = carregar_analyzer_engine(
    LISTA_ESTADOS_CAPITAIS_BR,
    TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR,
    LISTA_NOMES_COMUNS,
    LISTA_ESTADO_CIVIL,
    LISTA_ORGANIZACOES_CONHECIDAS,
    LISTA_TERMOS_COMUNS,
    LISTA_TITULOS_LEGAIS,
)
anonymizer_engine = carregar_anonymizer_engine()
operadores = obter_operadores_anonimizacao()


def executar_anonimizacao(
    texto_original,
    nomes_pf_metadados=None,
    retornar_metricas=False,
    nomes_manuais=None,
    nao_tarjar=None,
):
    """Executa o pipeline de anonimização no texto fornecido.

    nomes_manuais: nomes (ou palavras soltas) a tarjar onde aparecerem, além do que o motor encontra.
    nao_tarjar: trechos que não devem ser tarjados em nenhuma passagem; valem mais que nomes_manuais.
    """
    return executar_pipeline_anonimizacao(
        texto_original=texto_original,
        analyzer_engine=analyzer_engine,
        anonymizer_engine=anonymizer_engine,
        operadores=operadores,
        aplicar_nomes_pf_metadados_fn=aplicar_nomes_pf_metadados,
        nomes_pf_metadados=nomes_pf_metadados or set(),
        extrair_nomes_parte_alvo_fn=extrair_nomes_parte_alvo,
        extrair_nomes_papel_penal_fn=extrair_nomes_papel_penal,
        extrair_nomes_pessoais_contextuais_fn=extrair_nomes_pessoais_contextuais,
        aplicar_nomes_extraidos_fn=aplicar_nomes_extraidos,
        aplicar_sobrenomes_raros_fn=aplicar_sobrenomes_raros,
        aplicar_lista_nomes_comuns_fn=aplicar_lista_nomes_comuns,
        lista_nomes_comuns=LISTA_NOMES_COMUNS,
        filtrar_resultados_analise_fn=filtrar_resultados_analise,
        normalizar_placeholders_nome_parte_fn=normalizar_placeholders_nome_parte,
        placeholder_nome_parte_interno=PLACEHOLDER_NOME_PARTE_INTERNO,
        retornar_metricas=retornar_metricas,
        spans_nao_tarjar_fn=spans_nao_tarjar,
        nao_tarjar=nao_tarjar or [],
        spans_nomes_manuais_fn=spans_nomes_manuais,
        nomes_manuais=nomes_manuais or [],
        spans_agentes_publicos_fn=spans_agentes_publicos,
    )
