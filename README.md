---
title: Anonimizador Sinergia
emoji: 👁️
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 6.0.0
app_file: app.py
pinned: false
license: mit
short_description: Anonimizador de dados do Projeto Sinergia
---

# Anonimizador Sinergia

Aplicação de anonimização de textos e documentos jurídicos em português (pt-BR), com **Interface Web Nativa (HTML5 / CSS3 / JavaScript)** como padrão oficial, interface secundária em **Gradio** e motor híbrido de alta precisão baseado em:

- **Regras determinísticas (regex + listas de domínio)**
- **Reconhecimento de entidades com Presidio + spaCy (`pt_core_news_lg`)**
- **Pós-filtro de precisão para reduzir falso positivo em CPF, OAB e IDs**

O foco do projeto é anonimizar dados pessoais sensíveis (LGPD) preservando a integridade e o contexto técnico processual.

## Sumário

- [1. Objetivo e Escopo](#1-objetivo-e-escopo)
- [2. Arquitetura](#2-arquitetura)
- [3. Fluxo de Anonimização](#3-fluxo-de-anonimização)
- [4. Entidades e Operadores](#4-entidades-e-operadores)
- [5. Estratégia de Nomes (PF x PJ)](#5-estratégia-de-nomes-pf-x-pj)
- [6. Estrutura de Pastas](#6-estrutura-de-pastas)
- [7. Requisitos e Setup Local](#7-requisitos-e-setup-local)
- [8. Como Usar (Guia de Execução)](#8-como-usar-guia-de-execução)
  - [8.1 Opção A: Subir o Microserviço REST Isolado (Porta 8000)](#81-opção-a-subir-o-microserviço-rest-isolado-porta-8000)
  - [8.2 Opção B: Subir a Aplicação Completa com Frontend (Porta 7860)](#82-opção-b-subir-a-aplicação-completa-com-frontend-porta-7860)
  - [8.3 Resumo Comparativo das Opções](#83-resumo-comparativo-das-opções)
  - [8.4 URLs e Endpoints (Local e Nuvem)](#84-urls-e-endpoints-local-e-nuvem)
- [9. Testes e Validação](#9-testes-e-validação)
- [10. Ajustes e Extensibilidade](#10-ajustes-e-extensibilidade)
- [11. Limitações Conhecidas](#11-limitações-conhecidas)
- [12. Troubleshooting](#12-troubleshooting)
- [13. Guia de Implementação do Motor de Anonimização (Nível Engenharia)](#13-guia-de-implementação-do-motor-de-anonimização-nível-engenharia)
- [Referência de Desenvolvimento](#referência-de-desenvolvimento)

## 1. Objetivo e Escopo

### Objetivo principal

Anonimizar conteúdo jurídico em múltiplos formatos (texto livre, PDF com texto pesquisável e documentos Word `.docx`), preservando a legibilidade processual e os termos de interesse do Judiciário.

### Escopo funcional atual

- **Entrada Omnimodal:**
  - **Texto direto** (digitação ou colagem na interface)
  - **PDF textual** (extração por PyMuPDF)
  - **Documentos Word (.docx)** (extração de parágrafos e tabelas via `python-docx`)
- **Interfaces de Usuário:**
  - **Interface Web Nativa (Padrão Oficial):** SPA moderna servida na raiz (`/`), com realce visual de entidades (*highlighting*), alternância de tema (Claro/Escuro) e download de documento.
  - **Interface Gradio (Secundária / Alternativa):** Acessível em `/ui/`.
- **API HTTP RESTful dedicada:**
  - `POST /api/v1/anonimizar`: Endpoint JSON para anonimização de textos livres e metadados.
  - `POST /api/v1/anonimizar-arquivo`: Endpoint universal para upload de arquivos PDF e DOCX via `multipart/form-data`.
  - `POST /api/v1/pdf-tarjado`: Devolve o próprio PDF com tarja preta sobre os dados retirados.
  - `POST /anonimizar`: Rota de compatibilidade retroativa para clientes legados.
- **Saídas estruturadas:**
  - Texto anonimizado com substituições parametrizadas (`<CPF/CIN>`, `<ENDERECO>`, `<NOME>`, etc.).
  - Tabela detalhada de auditoria com spans, pontuação de confiança (*score*) e tipologia de cada entidade detectada.
  - Resumo de telemetria e tempo de processamento.

## 2. Arquitetura

A aplicação está modularizada em camadas para isolar responsabilidades de API, interfaces, regras de negócio e processamento de NLP.

### 2.1 Servidores HTTP e Pontos de Entrada

A aplicação oferece dois pontos de entrada independentes para atender a diferentes casos de uso:

1. **Aplicação Completa (`app.py` - Porta 7860):**
   - Servidor assíncrono baseado em **FastAPI + Uvicorn**.
   - Serve a **Interface Web Nativa SPA** (`static/index.html`, `static/css/`, `static/js/`) na raiz (`/`).
   - Monta a **Interface Gradio** na rota `/ui` através de `gr.mount_gradio_app`.
   - Expõe a API RESTful universal com suporte a CORS:
     - `POST /api/v1/anonimizar` (texto livre via JSON)
     - `POST /api/v1/anonimizar-arquivo` (PDF e Word `.docx` via upload multipart)
     - `POST /api/v1/pdf-tarjado` (PDF original com tarja preta sobre os dados retirados)
     - `POST /anonimizar` (compatibilidade retroativa)

2. **Microserviço REST Isolado (`api_anonimizador.py` - Porta 8000):**
   - Servidor FastAPI enxuto e estritamente focado em API (*headless*).
   - Sem carregamento de dependências de interface gráfica (Gradio/HTML/CSS), reduzindo consumo de memória e tempo de boot.
   - Ideal para integração backend com sistemas externos (Node.js, C#, Java, microsserviços judiciais).
   - Expõe `POST /api/v1/anonimizar`, `GET /health` e documentação Swagger `/docs`.

### 2.2 Núcleo (`core/`)

- `core/anonymizer_service.py`
  - Camada de serviço de NLP singleton e desacoplada de interfaces gráficas.
  - Inicializa uma única vez o `AnalyzerEngine` e o `AnonymizerEngine` (Presidio + spaCy).
  - Centraliza a função `executar_anonimizacao()`, consumida tanto por `app.py` quanto por `api_anonimizador.py`.

- `core/config.py`
  - Constantes globais e listas de controle (placeholders, papéis, indicadores PJ etc.)

- `core/resources.py`
  - Carregamento e indexação de arquivos de listas com codificação UTF-8:
    - `nomes_comuns.txt`
    - `termos_comuns.txt`
    - `titulos_legais.txt`
  - Definição de listas estáticas (estados/capitais, termos legais de cabeçalho etc.)

- `core/engine_setup.py`
  - Configuração do `AnalyzerEngine` (Presidio)
  - Registro de recognizers customizados (CPF, OAB, CEP, endereço, RG, CNH, SIAPE etc.)
  - Inicialização do `AnonymizerEngine`

- `core/operators.py`
  - Mapeamento entidade -> operador (`keep`, `replace`, `mask`)

- `core/text_filters.py`
  - Extração e filtragem de nomes
  - Regras de diferenciação PF/PJ
  - Etapa lexical por `nomes_comuns.txt`
  - Pós-filtro de resultados (validação/contexto CPF/OAB)

- `core/pipeline.py`
  - Orquestração linear do fluxo completo de anonimização

- `core/app_services.py`
  - Serviços de apoio (extração PDF com PyMuPDF, leitura DOCX, DataFrame de auditoria, telemetria)

- `core/ui_handlers.py`
  - Handlers de interação e callbacks da interface Gradio

- `core/interface_builder.py`
  - Construção da interface Gradio e injeção de CSS personalizado

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
├── app.py                      # Servidor FastAPI completo (SPA Web UI + Gradio + REST API universal)
├── api_anonimizador.py         # Microserviço REST isolado e headless (Porta 8000)
├── Dockerfile                  # Configuração multi-serviço para container Linux
├── docker-compose.yml          # Orquestração do microserviço (porta 8000) e app completo (porta 7860)
├── .dockerignore               # Arquivos e pastas excluídos do build do container
├── requirements.txt            # Dependências Python do backend, NLP e interface
├── nomes_comuns.txt            # Dicionário de prenomes e sobrenomes para varredura lexical
├── termos_comuns.txt           # Dicionário de termos comuns para evitar falsos positivos
├── titulos_legais.txt          # Termos legais e papéis processuais protegidos
├── core/
│   ├── anonymizer_service.py   # Serviço central desacoplado de inicialização de Presidio + spaCy
│   ├── app_services.py         # Extração de PDF/DOCX e formatação de telemetria
│   ├── config.py               # Constantes globais, regexes e listas de exclusão PJ
│   ├── engine_setup.py         # Configuração dos motores Presidio + spaCy
│   ├── interface_builder.py    # Definição dos componentes da UI Gradio
│   ├── operators.py            # Mapeamento de operadores e tags de substituição
│   ├── pipeline.py             # Orquestrador linear das fases de anonimização
│   ├── resources.py            # Carregamento e indexação das listas/dicionários
│   ├── text_filters.py         # Heurísticas PF/PJ, regex contextuais e pós-filtros
│   ├── ui_handlers.py          # Callbacks de interação da interface Gradio
│   └── __init__.py
├── static/                     # Interface Web Nativa (SPA moderna)
│   ├── index.html              # Estrutura HTML5 da interface padrão
│   ├── css/
│   │   └── styles.css          # Estilização com design system e tema dark/light
│   ├── js/
│   │   └── app.js              # Lógica do frontend em Vanilla JS (fetch assíncrono)
│   └── img/
│       └── logo.png            # Logotipo oficial do Projeto Sinergia TRF1
└── tests/
    ├── smoke_test_api.py       # Smoke test automatizado para validação rápida da API REST
    └── regression/             # Suíte de testes de regressão por snapshot
        ├── cases.json
        ├── baseline_snapshot.json
        ├── run_baseline.py
        └── README.md
```

## 7. Requisitos e Setup Local

### 7.1 Requisitos de Sistema

- **Python:** 3.10 a 3.14 (compatível com os wheels pré-compilados do ecossistema)
- **RAM Recomendada:** Mínimo de 2 GB livres (para carregamento do modelo spaCy `pt_core_news_lg` em memória)
- **Docker e Docker Compose:** (Opcional) para execução em containers

### 7.2 Dependências Python

Definidas em `requirements.txt`:

- `pandas==2.3.1`
- `PyMuPDF==1.26.3`
- `python-docx==1.2.0`
- `python-dotenv==1.1.1`
- `presidio-analyzer==2.2.359`
- `presidio-anonymizer==2.2.359`
- `spacy==3.8.7`
- `pt_core_news_lg` (modelo spaCy pt-BR grande pré-treinado)
- `fastapi==0.141.1`
- `uvicorn[standard]==0.52.4`
- `gradio==6.0.0` (deve coincidir com `sdk_version` no cabeçalho deste README)

As versões são fixadas de propósito: o baseline de regressão (`tests/regression/`) foi gerado com elas, e qualquer atualização deve ser seguida de `run_baseline.py verify`.

> [!NOTE]
> **Decisão sobre a versão do Gradio (out/2026):** o Gradio fica fixado em `6.0.0`, a mesma versão declarada em `sdk_version`, para não alterar o ambiente que já roda em produção no Hugging Face Spaces. Uma versão mais nova (6.25.0) foi testada localmente com sucesso, mas a atualização foi adiada de forma deliberada. Para atualizar no futuro, altere **os dois lugares ao mesmo tempo** (`requirements.txt` e `sdk_version`) e rode o smoke test e a regressão; se só um deles mudar, o pip troca a versão instalada pelo Space logo após o build.

### 7.3 Instalação Passo a Passo

```bash
# 1. Clonar o repositório
git clone https://github.com/rgsouza2024/anonimizador_sinergia.git
cd anonimizador_sinergia

# 2. Criar o ambiente virtual
python -m venv .venv

# 3. Ativar o ambiente virtual
# No Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# No Linux / macOS:
source .venv/bin/activate

# 4. Atualizar o pip e instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
```

> [!TIP]
> Para validar se o ambiente foi configurado corretamente sem precisar subir servidores, execute o smoke test rápido:
> ```bash
> python tests/smoke_test_api.py
> ```

## 8. Como Usar (Guia de Execução)

A aplicação pode ser executada de duas formas principais, dependendo do seu objetivo de uso:

---

### 8.1 Opção A: Subir o Microserviço REST Isolado (Porta 8000)

Esta opção é indicada para:
- **Integração com outros sistemas e linguagens** (Node.js, C#/.NET, Java, Go, PHP, etc.);
- **Uso em pipelines automatizados de ETL ou microsserviços judiciais**;
- **Cenários de consumo mínimo de memória**, pois não inicializa componentes de interface gráfica (Gradio ou HTML).

#### Como Iniciar:

**Via Python local:**
```bash
python api_anonimizador.py
```

**Via Docker Compose:**
```bash
docker compose up -d --build
```

#### URLs e Documentação:
- **Documentação OpenAPI / Swagger:** `http://localhost:8000/docs`
- **Documentação ReDoc:** `http://localhost:8000/redoc`
- **Healthcheck de Monitoramento:** `http://localhost:8000/health`

#### Endpoints Disponíveis:

##### 1. Healthcheck (`GET /health`)
Verifica se o microserviço está operando e se os motores spaCy/Presidio estão devidamente carregados na memória:
```bash
curl -X GET "http://localhost:8000/health"
```
*Resposta de exemplo:*
```json
{
  "status": "ok",
  "analyzer_carregado": true,
  "anonymizer_carregado": true
}
```

##### 2. Anonimização de Texto (`POST /api/v1/anonimizar`)
Recebe um texto em formato JSON e devolve o texto anonimizado junto com a lista de entidades detectadas e tempo de processamento.

- **Requisição via cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/anonimizar" \
       -H "Content-Type: application/json; charset=utf-8" \
       -d '{
         "texto": "O reclamante Carlos Eduardo Souza, portador do CPF 123.456.789-00, reside na Rua das Palmeiras, 450.",
         "nomes_metadados": ["Carlos Eduardo Souza"]
       }'
  ```

- **Requisição via Python (`requests`):**
  ```python
  import requests

  payload = {
      "texto": "O reclamante Carlos Eduardo Souza, portador do CPF 123.456.789-00, reside na Rua das Palmeiras, 450.",
      "nomes_metadados": ["Carlos Eduardo Souza"]  # opcional
  }
  response = requests.post("http://localhost:8000/api/v1/anonimizar", json=payload)
  dados = response.json()

  print("Texto Anonimizado:", dados["texto_anonimizado"])
  print("Tempo de Processamento:", dados["tempo_processamento"], "s")
  ```

- **Exemplo de Resposta JSON:**
  ```json
  {
    "texto_anonimizado": "O reclamante <NOME>, portador do <CPF/CIN>, reside na <ENDERECO>.",
    "entidades_detectadas": [
      {
        "Entidade": "CPF",
        "Texto Detectado": "CPF 123.456.789-00",
        "Início": 39,
        "Fim": 57,
        "Score": "1.00"
      },
      {
        "Entidade": "ENDERECO_LOGRADOURO",
        "Texto Detectado": "Rua das Palmeiras, 450",
        "Início": 69,
        "Fim": 91,
        "Score": "0.90"
      }
    ],
    "tempo_processamento": 0.177
  }
  ```

---

### 8.2 Opção B: Subir a Aplicação Completa com Frontend (Porta 7860)

Esta opção é indicada para:
- **Usuários finais** (magistrados, servidores, advogados e analistas);
- **Uso interativo no navegador**, com comparação lado a lado entre original e anonimizado;
- **Upload e processamento direto de arquivos PDF e documentos Word (.docx)**;
- **Visualização com realce gráfico de entidades (*entity highlighting*) e modo escuro/claro**.

#### Como Iniciar:

**Via Python local:**
```bash
python app.py
```

**Via Docker Compose:**
```bash
docker compose --profile full up -d --build app-completo
```

#### URLs Disponíveis:
- **Interface Web Nativa SPA (Padrão Oficial):** `http://localhost:7860/`
- **Interface Gradio (Secundária / Alternativa):** `http://localhost:7860/ui`
- **Documentação Swagger:** `http://localhost:7860/docs`

#### Recursos e Endpoints Disponíveis:

##### 1. Interface Web Nativa (`http://localhost:7860/`)
- SPA moderna em HTML5/CSS3/JavaScript servida diretamente pelo FastAPI.
- Alternância instantânea de tema Claro/Escuro (*Dark/Light Mode*).
- Realce colorido de cada tipo de entidade detectada sobre o texto.
- Tabela interativa com estatísticas e filtros por tipo de dado sensível.
- Botão de cópia e download imediato do documento sanitizado.

##### 2. Upload de Arquivos PDF e Word DOCX (`POST /api/v1/anonimizar-arquivo`)
Endpoint universal que aceita documentos PDF e Word via `multipart/form-data`:

- **Exemplo via cURL:**
  ```bash
  curl -X POST "http://localhost:7860/api/v1/anonimizar-arquivo" \
       -F "file=@peticao_inicial.pdf"
  ```
  *(Também compatível com arquivos `.docx`: `-F "file=@sentenca.docx"`)*

- **Exemplo de Resposta:**
  ```json
  {
    "sucesso": true,
    "nome_arquivo": "peticao_inicial.pdf",
    "tipo_arquivo": "pdf",
    "texto_extraido": "Texto bruto lido do arquivo...",
    "texto_anonimizado": "Texto sanitizado...",
    "entidades_detectadas": [...],
    "metadados_pdf": {},
    "tempo_processamento": 0.452
  }
  ```

##### 3. PDF Tarjado (`POST /api/v1/pdf-tarjado`)
Recebe o mesmo PDF (`multipart/form-data`) e devolve o arquivo com tarja preta sobre cada dado retirado. Usa a redação do PyMuPDF: o texto sob a tarja é removido do arquivo (não fica apenas encoberto), o restante continua pesquisável e os metadados (autor, título, assunto) são apagados. Na Interface Web Nativa, o botão **Baixar PDF tarjado** aparece quando o documento processado é um PDF.

```bash
curl -X POST "http://localhost:7860/api/v1/pdf-tarjado" -F "file=@peticao_inicial.pdf" -o peticao_inicial_tarjado.pdf
```

Limites: texto dentro de imagem (PDF digitalizado sem OCR) não é lido nem tarjado; anotações e comentários do PDF não são tratados; em PDF que justifica o texto com o operador `Tw`, o texto restante pode se deslocar visualmente para baixo de uma tarja (o conteúdo removido continua correto).

##### 4. Revisão humana: `nomes_manuais` e `nao_tarjar`
Os endpoints de texto, de arquivo e de PDF tarjado (e o microserviço `api_anonimizador.py`) aceitam dois campos opcionais:

- `nomes_manuais`: nomes, ou palavras soltas, a tarjar onde aparecerem, além do que o motor encontra (sem diferença de maiúscula ou acento, inclusive perto de endereço ou dentro de nome de empresa);
- `nao_tarjar`: trechos que não devem ser tarjados em nenhuma passagem do documento. Valem mais que `nomes_manuais`. Se o trecho liberado for parte de um nome maior ("Lima" em "João Lima"), só ele fica: o resto do nome continua tarjado.

No JSON, são listas (`"nomes_manuais": ["Schietti"]`); em `multipart/form-data`, campos repetidos (`-F "nomes_manuais=Schietti" -F "nao_tarjar=926.511.422-72"`).

##### 5. Rota de Compatibilidade Retroativa (`POST /anonimizar`)
Mantida para garantir compatibilidade com sistemas legados que consumiam a versão inicial da API.

---

### 8.3 Resumo Comparativo das Opções

| Característica | Opção A: Microserviço REST Isolado | Opção B: Aplicação Completa |
| :--- | :--- | :--- |
| **Arquivo de Entrada** | `api_anonimizador.py` | `app.py` |
| **Porta Padrão** | `8000` | `7860` |
| **Comando Local** | `python api_anonimizador.py` | `python app.py` |
| **Comando Docker** | `docker compose up -d` | `docker compose --profile full up -d app-completo` |
| **Interface Web SPA** | ❌ Não | ✔️ Sim (`/`) |
| **Interface Gradio** | ❌ Não | ✔️ Sim (`/ui`) |
| **API Texto JSON** | ✔️ Sim (`/api/v1/anonimizar`) | ✔️ Sim (`/api/v1/anonimizar`) |
| **Upload PDF / DOCX** | ❌ Não | ✔️ Sim (`/api/v1/anonimizar-arquivo`) |
| **PDF tarjado** | ❌ Não | ✔️ Sim (`/api/v1/pdf-tarjado`) |
| **Healthcheck** | ✔️ Sim (`/health`) | Embutido no FastAPI |
| **Consumo de Memória** | Mais enxuto (~700 MB a 1 GB) | Completo (~1 GB a 1.4 GB) |
| **Público Alvo** | Sistemas externos, integrações, microsserviços | Usuários finais, servidores, analistas |

---

### 8.4 URLs e Endpoints (Local e Nuvem)

#### Ambiente Local
- **Opção A (API Isolada):**
  - Base: `http://localhost:8000`
  - Swagger: `http://localhost:8000/docs`
  - Health: `http://localhost:8000/health`
- **Opção B (App Completo):**
  - Web UI SPA: `http://localhost:7860/`
  - Gradio UI: `http://localhost:7860/ui/`
  - Swagger: `http://localhost:7860/docs`

#### Hugging Face Spaces (quando publicado)
- **Web UI Nativa:** `https://[seu-space].hf.space/`
- **Web UI Gradio:** `https://[seu-space].hf.space/ui/`
- **API Texto:** `POST https://[seu-space].hf.space/api/v1/anonimizar`
- **API Arquivo (PDF/DOCX):** `POST https://[seu-space].hf.space/api/v1/anonimizar-arquivo`
- **API PDF tarjado:** `POST https://[seu-space].hf.space/api/v1/pdf-tarjado`

## 9. Testes e Validação

O projeto dispõe de duas estratégias complementares de testes automatizados:

### 9.1 Smoke Test da API (Rápido)
Testa a integridade do microserviço REST, validação de esquemas Pydantic, healthcheck e pipeline de anonimização em segundos:

```bash
python tests/smoke_test_api.py
```

O PDF tarjado tem um smoke test próprio, que gera um PDF de teste, chama `/api/v1/pdf-tarjado` e confere que os dados saíram do arquivo, que o texto público ficou e que os metadados foram apagados:

```bash
python tests/smoke_test_pdf_tarjado.py
```

### 9.2 Teste de Regressão por Baseline (Snapshot)
A suíte de regressão garante que alterações nas listas ou heurísticas não provoquem vazamento de dados ou sobreanonimização acidental:

- **Executar verificação comparativa:**
  ```bash
  python tests/regression/run_baseline.py verify
  ```

- **Atualizar snapshot de baseline (quando a alteração for intencional):**
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

### Layout quebrado ou ícones gigantes (Hugging Face)

Isso costuma ocorrer por conflito de assets estáticos no Gradio 5/6. A solução adotada foi isolar o Gradio no caminho `/ui/` e garantir que o `sdk_version` no `README.md` esteja como `6.0.0` ou superior.

### Erro `TypeError: BlockContext.__init__() got an unexpected keyword argument 'theme'`

O Gradio 6 removeu parâmetros globais do construtor de `gr.Blocks`. A aplicação foi ajustada para definir `theme`, `title` e `css` como **atributos do objeto** `demo` após sua criação no `core/interface_builder.py`.

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
