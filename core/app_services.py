"""Application service helpers (non-UI)."""

import fitz  # PyMuPDF
import pandas as pd


def dataframe_entidades_vazio(colunas_entidades_detectadas):
    return pd.DataFrame(columns=colunas_entidades_detectadas)


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

