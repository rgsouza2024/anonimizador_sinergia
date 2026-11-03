"""Anonymization pipeline orchestration."""

import pandas as pd

from core.rastreio import TextoRastreado


def _trechos_trocados_presidio(texto, resultado_anonimizado_obj, resultados_analise, operadores):
    """Trechos do texto de entrada que o Presidio de fato alterou (depois de resolver conflitos).

    O Presidio informa as trocas com posicoes no texto de SAIDA. Aqui elas sao convertidas para a
    entrada e a conversao e conferida; se nao fechar, devolve todas as deteccoes que alteram texto
    (tarja a mais, nunca a menos).
    """
    saida = resultado_anonimizado_obj.text
    itens = sorted(resultado_anonimizado_obj.items, key=lambda item: item.start)
    trechos, pos_entrada, pos_saida = [], 0, 0
    for k, item in enumerate(itens):
        inicio = pos_entrada + (item.start - pos_saida)
        if texto[pos_entrada:inicio] != saida[pos_saida:item.start]:
            break
        if item.operator in ("keep", "mask"):
            fim = inicio + (item.end - item.start)
        else:
            proximo = itens[k + 1].start if k + 1 < len(itens) else len(saida)
            intervalo = saida[item.end:proximo]
            candidatos = sorted(
                {r.end for r in resultados_analise if r.entity_type == item.entity_type and r.start >= inicio and r.end > inicio},
                reverse=True,
            )
            fim = next((e for e in candidatos if texto[e:e + len(intervalo)] == intervalo), None)
            if fim is None:
                break
        if item.operator == "mask":
            trechos += [
                (inicio + i, inicio + i + 1)
                for i in range(fim - inicio)
                if texto[inicio + i] != saida[item.start + i]
            ]
        elif item.operator != "keep":
            trechos.append((inicio, fim))
        pos_entrada, pos_saida = fim, item.end
    else:
        if texto[pos_entrada:] == saida[pos_saida:]:
            return trechos
    return [
        (r.start, r.end)
        for r in resultados_analise
        if operadores.get(r.entity_type, operadores.get("DEFAULT")).operator_name != "keep"
    ]


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
    spans_nao_tarjar_fn=None,
    nao_tarjar=None,
    spans_nomes_manuais_fn=None,
    nomes_manuais=None,
):
    metricas_pipeline = {}
    # Cada fase de nome troca trechos do texto; o rastreio guarda a posicao de cada troca no original.
    rastreado = TextoRastreado(texto_original)
    # Revisao humana: "nao tarjar" vale mais que tudo; os nomes escritos a mao vem logo depois.
    if spans_nao_tarjar_fn and nao_tarjar:
        rastreado.proteger(spans_nao_tarjar_fn(texto_original, nao_tarjar))
    if spans_nomes_manuais_fn and nomes_manuais:
        rastreado.substituir(spans_nomes_manuais_fn(rastreado.texto, nomes_manuais), "<NOME>")
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
    # Deteccao que toca trecho marcado como "nao tarjar" e descartada.
    resultados_analise = [r for r in resultados_analise if not rastreado.toca_protegido(r.start, r.end)]
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
        # Trechos do texto original efetivamente trocados: base do PDF tarjado.
        trechos = [(troca["inicio"], troca["fim"]) for troca in rastreado.trocas]
        trechos += [
            rastreado.origem(inicio, fim)
            for inicio, fim in _trechos_trocados_presidio(
                texto_para_anonimizar, resultado_anonimizado_obj, resultados_analise, operadores
            )
        ]
        metricas_pipeline["trechos_tarjados"] = sorted(set(trechos))
        return texto_anonimizado, pd.DataFrame(dados_resultados), metricas_pipeline
    return texto_anonimizado, pd.DataFrame(dados_resultados)
