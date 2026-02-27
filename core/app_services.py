"""Application service helpers (non-UI)."""

import os

import fitz  # PyMuPDF
import pandas as pd

from core.config import LIMITE_PDF_MB, LIMITE_PDF_PAGINAS
from core.text_filters import extrair_nomes_pf_metadados_pdf


def dataframe_entidades_vazio(colunas_entidades_detectadas):
    return pd.DataFrame(columns=colunas_entidades_detectadas)


def gerar_resumo_processamento(df_resultados, origem, tempo_segundos=None, info_metadado_pdf=None):
    sufixo_tempo = ""
    if tempo_segundos is not None:
        sufixo_tempo = f" Tempo total: {tempo_segundos:.2f}s."
    sufixo_metadado = ""
    if str(origem).upper() == "PDF":
        identificado = False
        total_nomes = 0
        ocorrencias_forcadas = 0
        if isinstance(info_metadado_pdf, dict):
            identificado = bool(info_metadado_pdf.get("metadado_nome_identificado", False))
            total_nomes = int(info_metadado_pdf.get("metadado_nomes_pf_total", 0) or 0)
            ocorrencias_forcadas = int(info_metadado_pdf.get("metadado_ocorrencias_forcadas", 0) or 0)
        if identificado:
            sufixo_metadado = (
                f" Metadados (nomes PF): identificado ({total_nomes} nome(s)); "
                f"ocorrencias forcadas: {ocorrencias_forcadas}."
            )
        else:
            sufixo_metadado = " Metadados (nomes PF): nao identificado."
    if df_resultados is None or df_resultados.empty:
        return f"**Resumo ({origem}):** nenhuma entidade detectada.{sufixo_metadado}{sufixo_tempo}"
    total_entidades = len(df_resultados)
    tipos_unicos = df_resultados["Entidade"].nunique()
    top_tipos = df_resultados["Entidade"].value_counts().head(3)
    top_formatado = ", ".join([f"{entidade} ({qtde})" for entidade, qtde in top_tipos.items()])
    return (
        f"**Resumo ({origem}):** {total_entidades} entidades detectadas em "
        f"{tipos_unicos} tipos. Principais ocorrencias: {top_formatado}.{sufixo_metadado}{sufixo_tempo}"
    )


def extrair_texto_de_pdf(caminho_arquivo_pdf):
    texto_completo = ""
    nomes_pf_metadados = set()
    try:
        tamanho_arquivo_bytes = os.path.getsize(caminho_arquivo_pdf)
        limite_tamanho_bytes = LIMITE_PDF_MB * 1024 * 1024
        if tamanho_arquivo_bytes > limite_tamanho_bytes:
            return (
                None,
                f"O PDF excede o limite de {LIMITE_PDF_MB} MB.",
                set(),
            )

        with fitz.open(caminho_arquivo_pdf) as documento_pdf:
            if documento_pdf.page_count > LIMITE_PDF_PAGINAS:
                return (
                    None,
                    f"O PDF excede o limite de {LIMITE_PDF_PAGINAS} paginas.",
                    set(),
                )
            nomes_pf_metadados = extrair_nomes_pf_metadados_pdf(documento_pdf.metadata or {})
            for pagina in documento_pdf:
                texto_completo += pagina.get_text()
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}")
        return None, f"Erro ao extrair texto do PDF: {e}", set()
    if not texto_completo.strip():
        return None, "O PDF carregado nao contem texto extraivel.", nomes_pf_metadados
    return texto_completo, None, nomes_pf_metadados
