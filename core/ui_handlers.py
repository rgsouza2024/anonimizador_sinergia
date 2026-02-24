"""UI handler helpers for the Gradio application."""

import time

import gradio as gr


def atualizar_estado_botao_texto(texto_original):
    texto_valido = bool(texto_original and texto_original.strip())
    return gr.update(interactive=texto_valido)


def atualizar_estado_botao_pdf(arquivo_temp):
    return gr.update(interactive=arquivo_temp is not None)


def desativar_botao():
    return gr.update(interactive=False)


def processar_texto_area(
    texto_original,
    anonimizar_logica_fn,
    dataframe_entidades_vazio_fn,
    gerar_resumo_processamento_fn,
    estado_vazio_texto_anonimizado,
    resumo_vazio_texto,
):
    if not texto_original or not texto_original.strip():
        gr.Warning("Cole ou digite um texto antes de iniciar a anonimizaçao.")
        return estado_vazio_texto_anonimizado, dataframe_entidades_vazio_fn(), resumo_vazio_texto
    inicio_processamento = time.perf_counter()
    try:
        texto_anonimizado, df_resultados = anonimizar_logica_fn(texto_original)
        tempo_total = time.perf_counter() - inicio_processamento
        resumo_processamento = gerar_resumo_processamento_fn(df_resultados, "Texto", tempo_total)
        gr.Info("Texto da area anonimizado com sucesso!")
        return texto_anonimizado, df_resultados, resumo_processamento
    except Exception as e:
        gr.Error(f"Ocorreu um erro durante a anonimizaçao: {e}")
        tempo_total = time.perf_counter() - inicio_processamento
        return (
            "Nao foi possivel processar o texto.",
            dataframe_entidades_vazio_fn(),
            f"**Resumo:** erro no processamento. Tempo total: {tempo_total:.2f}s.",
        )


def limpar_texto_area(dataframe_entidades_vazio_fn, estado_vazio_texto_anonimizado, resumo_vazio_texto):
    return "", estado_vazio_texto_anonimizado, dataframe_entidades_vazio_fn(), resumo_vazio_texto, gr.update(interactive=False)


def processar_arquivo_pdf(
    arquivo_temp,
    anonimizar_logica_fn,
    extrair_texto_de_pdf_fn,
    gerar_resumo_processamento_fn,
    estado_vazio_pdf_original,
    estado_vazio_pdf_anonimizado,
    resumo_vazio_pdf,
    progress,
):
    if arquivo_temp is None:
        gr.Warning("Selecione um arquivo PDF antes de iniciar a anonimizaçao.")
        return estado_vazio_pdf_original, estado_vazio_pdf_anonimizado, resumo_vazio_pdf
    inicio_processamento = time.perf_counter()
    progress(0, desc="Iniciando...")
    try:
        progress(0.2, desc="Extraindo texto do PDF...")
        retorno_extracao = extrair_texto_de_pdf_fn(arquivo_temp.name)
        if isinstance(retorno_extracao, tuple) and len(retorno_extracao) == 3:
            texto_extraido, erro, nomes_pf_metadados = retorno_extracao
        else:
            texto_extraido, erro = retorno_extracao
            nomes_pf_metadados = set()

        if erro:
            gr.Error(erro)
            tempo_total = time.perf_counter() - inicio_processamento
            return (
                estado_vazio_pdf_original,
                estado_vazio_pdf_anonimizado,
                f"**Resumo:** erro na extraçao. Tempo total: {tempo_total:.2f}s.",
            )
        progress(0.6, desc="Anonimizando o conteudo...")
        retorno_anonimizacao = anonimizar_logica_fn(
            texto_extraido,
            nomes_pf_metadados,
            retornar_metricas=True,
        )
        if isinstance(retorno_anonimizacao, tuple) and len(retorno_anonimizacao) == 3:
            texto_anonimizado, df_resultados, metricas_pipeline = retorno_anonimizacao
        else:
            texto_anonimizado, df_resultados = retorno_anonimizacao
            metricas_pipeline = {}

        info_metadado_pdf = {}
        if isinstance(metricas_pipeline, dict):
            info_metadado_pdf = metricas_pipeline.get("metadado", {}) or {}

        tempo_total = time.perf_counter() - inicio_processamento
        resumo_processamento = gerar_resumo_processamento_fn(
            df_resultados,
            "PDF",
            tempo_total,
            info_metadado_pdf=info_metadado_pdf,
        )
        progress(1, desc="Concluido!")
        gr.Info("Arquivo PDF anonimizado com sucesso!")
        return texto_extraido, texto_anonimizado, resumo_processamento
    except Exception as e:
        gr.Error(f"Ocorreu um erro ao processar o PDF: {e}")
        tempo_total = time.perf_counter() - inicio_processamento
        return (
            estado_vazio_pdf_original,
            estado_vazio_pdf_anonimizado,
            f"**Resumo:** erro no processamento. Tempo total: {tempo_total:.2f}s.",
        )
