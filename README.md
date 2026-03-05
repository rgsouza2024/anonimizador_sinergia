---
title: Anonimizador Sinergia
emoji: 👁️
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 5.42.0
app_file: app.py
pinned: false
license: mit
short_description: Anonimizador de dados do Projeto Sinergia
---

# Anonimizador Sinergia

Aplicação de anonimização de textos jurídicos em português (pt-BR), com interface Gradio e motor híbrido baseado em:

- **Regras determinísticas (regex + listas de domínio)**
- **Reconhecimento de entidades com Presidio + spaCy**
- **Pós-filtro de precisão para reduzir falso positivo em CPF/OAB**

O foco do projeto é anonimizar dados pessoais sensíveis sem perder contexto jurídico essencial.

## Sumário

- [1. Objetivo e Escopo](#1-objetivo-e-escopo)
- [2. Arquitetura](#2-arquitetura)
- [3. Fluxo de Anonimização](#3-fluxo-de-anonimização)
- [4. Entidades e Operadores](#4-entidades-e-operadores)
- [5. Estratégia de Nomes (PF x PJ)](#5-estratégia-de-nomes-pf-x-pj)
- [6. Estrutura de Pastas](#6-estrutura-de-pastas)
- [7. Requisitos e Setup Local](#7-requisitos-e-setup-local)
- [8. Execução](#8-execução)
- [9. Testes de Regressão](#9-testes-de-regressão)
- [10. Ajustes e Extensibilidade](#10-ajustes-e-extensibilidade)
- [11. Limitações Conhecidas](#11-limitações-conhecidas)
- [12. Troubleshooting](#12-troubleshooting)

## 1. Objetivo e Escopo

### Objetivo principal

Anonimizar conteúdo jurídico (texto livre e PDF com texto pesquisável), preservando o máximo possível de legibilidade processual.

### Escopo funcional atual

- Entrada de **texto** (colar na interface)
- Entrada de **PDF textual** (extração por PyMuPDF)
- Saída com:
  - Texto anonimizado
  - Tabela de entidades detectadas
  - Resumo de processamento

### Fora de escopo (estado atual)

- OCR de PDF escaneado (imagem)
- **API HTTP dedicada**: endpoint `/api/v1/anonimizar` (JSON POST) para integração com outros sistemas.
- Garantia de 100% de cobertura sem revisão humana

## 2. Arquitetura

A aplicação está modularizada em camadas.

### 2.1 Ponto de entrada

- `app.py`
  - Inicializa engines e recursos
  - Injeta dependências nas funções de pipeline/UI
  - Sobe a interface Gradio

### 2.2 Núcleo (`core/`)

- `core/config.py`
  - Constantes globais e listas de controle (placeholders, papéis, indicadores PJ etc.)

- `core/resources.py`
  - Carregamento de arquivos de lista:
    - `nomes_comuns.txt`
    - `termos_comuns.txt`
    - `titulos_legais.txt`
  - Também define listas estáticas (estados/capitais, termos legais de cabeçalho etc.)

- `core/engine_setup.py`
  - Configuração do `AnalyzerEngine` (Presidio)
  - Registro de recognizers customizados (CPF, OAB, CEP, endereço, RG etc.)
  - Inicialização do `AnonymizerEngine`

- `core/operators.py`
  - Mapeamento entidade -> operador (`keep`, `replace`, `mask`)

- `core/text_filters.py`
  - Extração e filtragem de nomes
  - Regras PF/PJ
  - Etapa lexical por `nomes_comuns.txt`
  - Pós-filtro de resultados (validação/contexto CPF/OAB)

- `core/pipeline.py`
  - Orquestração completa do fluxo de anonimização

- `core/app_services.py`
  - Serviços de apoio (extração PDF, DataFrame vazio, resumo)

- `core/ui_handlers.py`
  - Handlers de interação da UI

- `core/interface_builder.py`
  - Construção da interface Gradio

## 3. Fluxo de Anonimização

Pipeline principal em `core/pipeline.py`:

1. **Extração de nomes de parte alvo**
   - Regex por papéis processuais em `core/text_filters.py`
   - Substituição por placeholder interno `__NOME_PARTE_AUTORA__`

2. **Extração de nomes contextuais**
   - Regex contextual (autor, requerido, réu, assinado por etc.)
   - Substituição por `<NOME>`

3. **Anonimização lexical por lista de nomes comuns**
   - Varredura token a token usando `nomes_comuns.txt`
   - Aplica `<NOME>` para tokens da lista
   - Com proteções para:
     - spans de pessoa jurídica
     - contexto de endereço

4. **Análise Presidio**
   - Executa recognizers para entidades sensíveis
   - Entidades de proteção/escudo também participam (`SAFE_LOCATION`, `LEGAL_HEADER`, `TERMO_COMUM`, etc.)

5. **Pós-filtro de qualidade**
   - CPF: valida dígito verificador ou contexto forte
   - OAB: exige contexto quando sem prefixo explícito

6. **Anonimização final por operadores**
   - `keep` / `replace` / `mask`

7. **Normalização de placeholder**
   - `__NOME_PARTE_AUTORA__` -> `<NOME_PARTE_AUTORA>`

8. **Geração da tabela de entidades**
   - Entidade, trecho detectado, início, fim, score

## 4. Entidades e Operadores

### 4.1 Operadores configurados (`core/operators.py`)

- `DEFAULT`: `keep`
- `PERSON`: `keep` (não usado na análise do pipeline atual)
- `LOCATION`: `keep`
- `ENDERECO_LOGRADOURO`: `replace` -> `<ENDERECO>`
- `EMAIL_ADDRESS`: `replace` -> `<EMAIL>`
- `PHONE_NUMBER`: `mask` (4 caracteres finais)
- `CPF`: `replace` -> `<CPF/CIN>`
- `DATE_TIME`: `keep`
- `OAB_NUMBER`: `replace` -> `<OAB>`
- `CEP_NUMBER`: `replace` -> `<CEP>`
- `ESTADO_CIVIL`: `keep`
- `ORGANIZACAO_CONHECIDA`: `keep`
- `ID_DOCUMENTO`: `keep`
- `LEGAL_TITLE`: `keep`
- `LEGAL_OR_COMMON_TERM`: `keep`
- `CNH`: `replace` -> `***********`
- `SIAPE`: `replace` -> `***`
- `RG_NUMBER`: `replace` -> `<NUMERO RG>`
- `MATRICULA_SIAPE`: `replace` -> `***`
- `TERMO_COMUM`: `keep`

### 4.2 Recognizers customizados (`core/engine_setup.py`)

Entidades custom registradas:

- `SAFE_LOCATION`
- `LEGAL_HEADER`
- `LEGAL_TITLE`
- `CPF`
- `OAB_NUMBER`
- `CEP_NUMBER`
- `ENDERECO_LOGRADOURO`
- `ESTADO_CIVIL`
- `ORGANIZACAO_CONHECIDA`
- `TERMO_COMUM`
- `CNH`
- `SIAPE`
- `RG_NUMBER`
- `MATRICULA_SIAPE`
- `ID_DOCUMENTO`

## 5. Estratégia de Nomes (PF x PJ)

### 5.1 Princípio adotado

- **Anonimizar pessoa física (PF) com prioridade**
- **Preservar pessoa jurídica (PJ) sempre que identificável**

### 5.2 Mecanismos usados

1. Filtros de plausibilidade PF (`_nome_parece_pessoa_fisica`)
2. Indicadores de PJ (`TERMOS_INDICADORES_PJ`)
3. Stopwords jurídicas (`PALAVRAS_NAO_NOME_GENERICAS`)
4. Proteção de spans de PJ antes da anonimização lexical
5. Bloqueio de anonimização lexical em contexto de endereço

### 5.3 Observação importante

A lista `nomes_comuns.txt` é propositalmente agressiva para reduzir vazamento de nomes, mas pode elevar sobreanonimização em textos com OCR ruidoso. A proteção PJ/endereço reduz, mas não elimina, esse efeito.

## 6. Estrutura de Pastas

```text
.
├── app.py
├── core/
│   ├── app_services.py
│   ├── config.py
│   ├── engine_setup.py
│   ├── interface_builder.py
│   ├── operators.py
│   ├── pipeline.py
│   ├── resources.py
│   ├── text_filters.py
│   ├── ui_handlers.py
│   └── __init__.py
├── tests/
│   └── regression/
│       ├── cases.json
│       ├── baseline_snapshot.json
│       ├── run_baseline.py
│       └── README.md
├── nomes_comuns.txt
├── termos_comuns.txt
├── titulos_legais.txt
├── requirements.txt
└── README.md
```

## 7. Requisitos e Setup Local

### 7.1 Dependências Python

Definidas em `requirements.txt`:

- `pandas==2.3.1`
- `PyMuPDF==1.26.3`
- `python-docx==1.2.0`
- `python-dotenv==1.1.1`
- `presidio-analyzer==2.2.359`
- `presidio-anonymizer==2.2.359`
- `spacy==3.8.7`
- modelo spaCy pt-BR via URL: `pt_core_news_lg-3.8.0`

### 7.2 Instalação recomendada

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## 8. Execução

```bash
python app.py
```

Se os motores carregarem corretamente, a aplicação abrirá a interface Gradio.

## 9. Testes de Regressão

A suíte atual é baseada em snapshot.

### 9.1 Rodar verificação

```bash
python tests/regression/run_baseline.py verify
```

### 9.2 Regerar baseline (quando mudança é intencional)

```bash
python tests/regression/run_baseline.py snapshot
```

### 9.3 O que é validado

- Texto anonimizado final
- Entidades detectadas e trechos correspondentes

## 10. Ajustes e Extensibilidade

### 10.1 Onde alterar regras de domínio

- `nomes_comuns.txt`: lista lexical agressiva para nomes
- `termos_comuns.txt`: termos jurídicos a preservar
- `titulos_legais.txt`: títulos/cargos legais

### 10.2 Onde alterar regex/entidades

- `core/engine_setup.py`: patterns e recognizers
- `core/operators.py`: política de output por entidade
- `core/text_filters.py`: heurística de nome PF/PJ e filtros contextuais

### 10.3 Como adicionar nova entidade

1. Criar recognizer em `core/engine_setup.py`
2. Definir operador em `core/operators.py`
3. Incluir caso de regressão em `tests/regression/cases.json`
4. Rodar `verify` e atualizar snapshot, se necessário

## 11. Limitações Conhecidas

- Não há OCR para PDFs escaneados (imagem pura)
- `PERSON` do spaCy não é usado diretamente no pipeline atual
- Qualidade do texto de entrada (OCR/encoding) impacta fortemente o recall
- Estratégia lexical por `nomes_comuns.txt` pode causar sobreanonimização em casos ambíguos

## 12. Troubleshooting

### `ERRO CRÍTICO: Modelo spaCy 'pt_core_news_lg' não encontrado`

Instale dependências novamente:

```bash
pip install -r requirements.txt
```

### PDF sem texto extraível

Se o app retornar "O PDF carregado não contém texto extraível", o arquivo provavelmente é imagem (sem camada textual). A versão atual não executa OCR.

### Resultado com excesso de `<NOME>`

Revisar:

- `nomes_comuns.txt` (remover entradas excessivamente genéricas)
- `TERMOS_INDICADORES_PJ` em `core/config.py`
- `PALAVRAS_NAO_NOME_GENERICAS` em `core/config.py`

---

## Nota de segurança

Mesmo com as regras atuais, nenhum motor de anonimização garante cobertura absoluta em documentos jurídicos complexos. Sempre realizar revisão humana antes de compartilhamento externo.

## 13. Guia de Implementação do Motor de Anonimização (Nível Engenharia)

Esta seção descreve como projetar e implementar um motor de anonimização híbrido (determinístico + NER), com foco em textos jurídicos de alta variabilidade.

### 13.1 Contrato de I/O e invariantes

Defina um contrato explícito para o pipeline:

- `input`: `str` bruto (UTF-8, potencialmente com ruído de OCR)
- `output`:
  - `text_anon`: texto final anonimizado
  - `detections`: tabela estruturada com `{entity, span_start, span_end, raw_text, score, source}`

Invariantes recomendadas:

- preservar offset lógico entre fases (ou manter mapa de offsets se houver expansão/contração de texto);
- todas as substituições devem ser reprodutíveis com a mesma configuração;
- nenhuma fase deve depender de estado global mutável.

### 13.2 Arquitetura em estágios (DAG linear)

Modelo de referência:

1. `normalize_input` (normalização leve e não destrutiva)
2. `pre_anonymize_rules` (regras de nomes contextuais e listas agressivas)
3. `entity_detection` (Presidio/spaCy + regex entities)
4. `post_filter` (validação contextual e semântica)
5. `operator_apply` (replace/mask/keep)
6. `reporting` (telemetria + tabela de entidades)

Cada estágio deve receber e retornar objetos imutáveis (ou cópia defensiva), por exemplo:

```python
from dataclasses import dataclass
from typing import List, Literal

@dataclass(frozen=True)
class Detection:
    entity: str
    start: int
    end: int
    score: float
    source: Literal["regex", "ner", "list", "post_filter"]

@dataclass(frozen=True)
class PipelineState:
    text: str
    detections: List[Detection]
```

### 13.3 Estratégia híbrida: determinístico primeiro, NER depois

Para domínio jurídico, deterministic-first tende a ser superior em previsibilidade:

- **Pré-anonimização de nomes**:
  - regras estruturais (`AUTOR:`, `REQUERIDO:`, `(... REU)`);
  - heurísticas contextuais (`assinado eletronicamente por`, `advogado`, etc.);
  - lista lexical (`nomes_comuns.txt`) como camada de segurança.
- **Detecção Presidio/NER**:
  - entidades documentais e numéricas (CPF, OAB, CEP, RG, SIAPE, CNH);
  - endereços por regex de logradouro.

Motivo técnico: nomes em petições têm alta variação de formatação e ruído; antecipar essa anonimização reduz vazamento antes do NER.

### 13.4 Controle de falso positivo por “guardrails”

Qualquer lista agressiva de nomes deve operar com guardrails:

- bloqueio por spans de PJ (razão social/órgãos);
- bloqueio por contexto de endereço (para não quebrar `ENDERECO_LOGRADOURO`);
- stoplist de léxico jurídico para evitar `<NOME>` em termos abstratos.

Formalmente, trate cada candidato como decisão binária:

`mask = (in_name_list AND not_in_pj_span AND not_address_context AND not_stopword)`

### 13.5 Modelo de entidades e precedência

Padronize precedência de conflitos em sobreposição de spans:

1. `protect` (entidades que devem permanecer, ex.: `TERMO_COMUM`, `LEGAL_TITLE`)
2. `hard_mask` (CPF/OAB/RG/ENDERECO)
3. `soft_mask` (nomes por heurística/lista)
4. `default_keep`

Quando duas entidades colidem, resolva por:

- prioridade estática (acima), depois
- score, depois
- maior comprimento de span.

### 13.6 Operadores de anonimização como política externa

Separe detecção de transformação:

- detecção diz “o que é”
- operador diz “como anonimizar”

Exemplo de tabela de política:

- `replace("<CPF/CIN>")`
- `replace("<OAB>")`
- `mask(chars_to_mask=4, from_end=True)` para telefone
- `keep` para entidades de preservação

Isso permite trocar comportamento sem tocar recognizers.

### 13.7 Normalização e matching robusto

Em textos judiciais, implemente matching:

- case-insensitive;
- accent-insensitive (`NFKD`);
- whitespace-flexible;
- boundary-safe (`(?<!\w)` / `(?!\w)`).

Evite normalização destrutiva global do texto antes do cálculo de spans. Normalize apenas no matching.

### 13.8 Pós-filtro semântico de precisão

Após detectar, faça validação por entidade:

- **CPF**: dígito verificador ou contexto forte (`CPF`, `CIN`, etc.)
- **OAB**: se formato compacto sem prefixo, exigir contexto jurídico próximo
- **IDs longos**: manter como `ID_DOCUMENTO` quando for número processual/documental

Esse estágio é o principal redutor de falso positivo em produção.

### 13.9 Performance e escalabilidade

Boas práticas:

- compile regex uma vez (módulo/boot);
- pré-indexe listas lexicais em `set` normalizado;
- use multi-pattern matching (Aho-Corasick) se o dicionário crescer;
- evite múltiplas passagens completas no texto quando possível;
- meça tempo por estágio (`perf_counter`).

KPIs úteis:

- `latency_p50/p95` por tamanho de texto;
- `detections_per_entity`;
- taxa de pós-filtro (`raw -> accepted`).

### 13.10 Qualidade: baseline de regressão e mudança controlada

Para motores baseados em regras, snapshot testing é obrigatório:

- corpus representativo com casos positivos e negativos;
- baseline versionada;
- toda alteração de regra deve atualizar baseline apenas quando mudança for intencional.

Matriz mínima de testes:

- PF deve anonimizar;
- PJ deve permanecer;
- endereço deve virar `<ENDERECO>`;
- OAB/CPF devem respeitar contexto e validação;
- termos jurídicos não podem virar `<NOME>`.

### 13.11 Observabilidade e auditoria técnica

Produza trilha auditável por execução:

- versão do motor (git SHA);
- configuração carregada (hash das listas e regex-set);
- número de entidades por tipo;
- amostra de decisões de pós-filtro (sem logar texto sensível completo).

Para investigação de regressão, isso reduz muito MTTR.

### 13.12 Segurança e governança

Regras de operação recomendadas:

- anonimização server-side (não confiar em cliente);
- descarte de artefatos temporários de texto bruto;
- revisão humana antes de compartilhamento externo;
- política de classificação de risco por documento;
- aprovação formal para mudanças em listas críticas (`nomes_comuns.txt`, `termos_comuns.txt`).

Em ambiente regulado, trate o motor como componente de segurança de dados, com controle de versão, revisão por pares e trilha de auditoria.

---

## Referência de desenvolvimento

Desenvolvimento e direção técnica: **Rodrigo Gonçalves de Souza**, **Juiz Federal do TRF da 1ª Região**.
