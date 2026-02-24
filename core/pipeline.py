"""Anonymization pipeline orchestration."""

import pandas as pd


def executar_pipeline_anonimizacao(
    texto_original,
    analyzer_engine,
    anonymizer_engine,
    operadores,
    anonimizar_nomes_pf_metadados_fn,
    nomes_pf_metadados,
    extrair_nomes_parte_alvo_fn,
    extrair_nomes_pessoais_contextuais_fn,
    anonimizar_nomes_extraidos_fn,
    anonimizar_por_lista_nomes_comuns_fn,
    lista_nomes_comuns,
    filtrar_resultados_analise_fn,
    normalizar_placeholders_nome_parte_fn,
    placeholder_nome_parte_interno,
    retornar_metricas=False,
):
    metricas_pipeline = {}
    if retornar_metricas:
        texto_preprocessado, metricas_metadado = anonimizar_nomes_pf_metadados_fn(
            texto_original,
            nomes_pf_metadados,
            "<NOME>",
            retornar_metricas=True,
        )
        metricas_pipeline["metadado"] = metricas_metadado
    else:
        texto_preprocessado = anonimizar_nomes_pf_metadados_fn(
            texto_original,
            nomes_pf_metadados,
            "<NOME>",
        )
    nomes_parte_alvo = extrair_nomes_parte_alvo_fn(texto_original)
    texto_para_anonimizar = anonimizar_nomes_extraidos_fn(
        texto_preprocessado,
        nomes_parte_alvo,
        placeholder_nome_parte_interno,
    )
    nomes_contextuais = extrair_nomes_pessoais_contextuais_fn(texto_para_anonimizar)
    texto_para_anonimizar = anonimizar_nomes_extraidos_fn(
        texto_para_anonimizar,
        nomes_contextuais,
        "<NOME>",
    )
    texto_para_anonimizar = anonimizar_por_lista_nomes_comuns_fn(
        texto_para_anonimizar,
        lista_nomes_comuns,
        "<NOME>",
    )
    entidades_para_analise = list(operadores.keys()) + [
        "SAFE_LOCATION",
        "LEGAL_HEADER",
        "ESTADO_CIVIL",
        "ORGANIZACAO_CONHECIDA",
        "ID_DOCUMENTO",
        "CNH",
        "SIAPE",
        "MATRICULA_SIAPE",
    ]
    entidades_para_analise = list(set(entidades_para_analise) - {"DEFAULT", "PERSON"})
    resultados_analise_brutos = analyzer_engine.analyze(
        text=texto_para_anonimizar,
        language="pt",
        entities=entidades_para_analise,
        return_decision_process=False,
    )
    resultados_analise = filtrar_resultados_analise_fn(resultados_analise_brutos, texto_para_anonimizar)
    resultado_anonimizado_obj = anonymizer_engine.anonymize(
        text=texto_para_anonimizar,
        analyzer_results=resultados_analise,
        operators=operadores,
    )
    texto_anonimizado = normalizar_placeholders_nome_parte_fn(resultado_anonimizado_obj.text)
    dados_resultados = [
        {
            "Entidade": res.entity_type,
            "Texto Detectado": normalizar_placeholders_nome_parte_fn(texto_para_anonimizar[res.start:res.end]),
            "Início": res.start,
            "Fim": res.end,
            "Score": f"{res.score:.2f}",
        }
        for res in sorted(resultados_analise, key=lambda x: x.start)
    ]
    if retornar_metricas:
        return texto_anonimizado, pd.DataFrame(dados_resultados), metricas_pipeline
    return texto_anonimizado, pd.DataFrame(dados_resultados)
