"""Anonymization pipeline orchestration."""

import pandas as pd

from core.rastreio import TextoRastreado


def executar_pipeline_anonimizacao(
    texto_original,
    analyzer_engine,
    anonymizer_engine,
    operadores,
    aplicar_nomes_pf_metadados_fn,
    nomes_pf_metadados,
    extrair_nomes_parte_alvo_fn,
    extrair_nomes_papel_penal_fn,
    extrair_nomes_pessoais_contextuais_fn,
    aplicar_nomes_extraidos_fn,
    aplicar_sobrenomes_raros_fn,
    aplicar_lista_nomes_comuns_fn,
    lista_nomes_comuns,
    filtrar_resultados_analise_fn,
    normalizar_placeholders_nome_parte_fn,
    placeholder_nome_parte_interno,
    retornar_metricas=False,
):
    metricas_pipeline = {}
    # Cada fase de nome troca trechos do texto; o rastreio guarda a posicao de cada troca no original.
    rastreado = TextoRastreado(texto_original)
    metricas_metadado = aplicar_nomes_pf_metadados_fn(rastreado, nomes_pf_metadados, "<NOME>")
    if retornar_metricas:
        metricas_pipeline["metadado"] = metricas_metadado

    nomes_parte_alvo = extrair_nomes_parte_alvo_fn(texto_original)
    aplicar_nomes_extraidos_fn(rastreado, nomes_parte_alvo, placeholder_nome_parte_interno)
    aplicar_sobrenomes_raros_fn(rastreado, nomes_parte_alvo, lista_nomes_comuns, placeholder_nome_parte_interno)

    nomes_papel_penal = extrair_nomes_papel_penal_fn(texto_original)
    aplicar_nomes_extraidos_fn(rastreado, nomes_papel_penal, "<NOME>")
    aplicar_sobrenomes_raros_fn(rastreado, nomes_papel_penal, lista_nomes_comuns, "<NOME>")

    nomes_contextuais = extrair_nomes_pessoais_contextuais_fn(rastreado.texto)
    aplicar_nomes_extraidos_fn(rastreado, nomes_contextuais, "<NOME>")
    aplicar_sobrenomes_raros_fn(rastreado, nomes_contextuais, lista_nomes_comuns, "<NOME>")

    aplicar_lista_nomes_comuns_fn(rastreado, lista_nomes_comuns, "<NOME>")

    texto_para_anonimizar = rastreado.texto
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
    # Deteccao inteira dentro de um marcador ja aplicado ("NOME" em <NOME>) e ruido.
    resultados_analise = [r for r in resultados_analise if not rastreado.dentro_de_marcador(r.start, r.end)]
    resultado_anonimizado_obj = anonymizer_engine.anonymize(
        text=texto_para_anonimizar,
        analyzer_results=resultados_analise,
        operators=operadores,
    )
    texto_anonimizado = normalizar_placeholders_nome_parte_fn(resultado_anonimizado_obj.text)

    # Auditoria com posicoes no texto original: trocas de nome e deteccoes do Presidio.
    dados_resultados = [
        {
            "Entidade": troca["valor"].strip("<>_"),
            "Texto Detectado": texto_original[troca["inicio"]:troca["fim"]],
            "Início": troca["inicio"],
            "Fim": troca["fim"],
            "Score": "1.00",
        }
        for troca in rastreado.trocas
    ]
    for res in resultados_analise:
        inicio, fim = rastreado.origem(res.start, res.end)
        dados_resultados.append(
            {
                "Entidade": res.entity_type,
                "Texto Detectado": texto_original[inicio:fim],
                "Início": inicio,
                "Fim": fim,
                "Score": f"{res.score:.2f}",
            }
        )
    dados_resultados.sort(key=lambda linha: (linha["Início"], -linha["Fim"]))
    if retornar_metricas:
        return texto_anonimizado, pd.DataFrame(dados_resultados), metricas_pipeline
    return texto_anonimizado, pd.DataFrame(dados_resultados)
