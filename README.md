---
title: Anonimizador Sinergia
emoji: ð
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 5.42.0
app_file: app.py
pinned: false
license: mit
short_description: Anonimizador de dados do Projeto Sinergia
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

**Mapa entidade por entidade (motor atual em `app.py`)**

Referência principal: `app.py:66`, `app.py:152`, `app.py:243`.

| Entidade | O que detecta | Regex/lista usada | Output final |
|---|---|---|---|
| `PERSON` | Nomes de pessoas (NER + sobrenomes frequentes) | Regex dinâmica por sobrenome: `(?i)\b{sobrenome}\b` + recognizer spaCy | `replace` -> `<NOME>` |
| `LOCATION` | Localizações (spaCy NER) | Sem regex no app (recognizer padrão) | `replace` -> `<ENDERECO>` |
| `EMAIL_ADDRESS` | E-mails | Sem regex no app (recognizer padrão Presidio) | `replace` -> `<EMAIL>` |
| `PHONE_NUMBER` | Telefones | Sem regex no app (recognizer padrão Presidio) | `mask` -> mascara 4 chars finais com `*` |
| `DATE_TIME` | Datas/horários | Sem regex no app (recognizer padrão Presidio) | `keep` |
| `CPF` | CPF formatado | `\b\d{3}\.\d{3}\.\d{3}-\d{2}\b` | `replace` -> `<CPF>` |
| `OAB_NUMBER` | Número OAB (com/sem prefixo) | `\b(?:OAB\s+)?\d{1,6}(?:\.\d{3})?\s*\/\s*[A-Z]{2}\b` | `replace` -> `<OAB>` |
| `CEP_NUMBER` | CEP com/sem pontuação | `\b(\d{5}-?\d{3}|\d{2}\.\d{3}-?\d{3})\b` | `replace` -> `<CEP>` |
| `CNH` | CNH formatada ou 11 dígitos isolados | `\bCNH\s*(?:nº|n\.)?\s*\d{11}\b` e `\b(?<![\w])\d{11}(?![\w])\b` | `replace` -> `***********` |
| `SIAPE` | SIAPE formatado ou 7 dígitos isolados | `\bSIAPE\s*(?:nº|n\.)?\s*\d{7}\b` e `\b(?<![\w])\d{7}(?![\w])\b` | `replace` -> `***` |
| `CI` | Carteira de identidade (CI) | `\bCI\s*(?:nº|n\.)?\s*[\d.]{7,11}-?\d\b` e `\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b` | `replace` -> `***` |
| `CIN` | Carteira de identidade nacional (CIN) | `\bCIN\s*(?:nº|n\.)?\s*[\d.]{7,11}-?\d\b` e `\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b` | `replace` -> `***` |
| `RG_NUMBER` | RG com prefixo/formato completo ou simples | `\bRG\s*(?:nº|n\.)?\s*[\d.X-]+(?:-\dª\s*VIA)?\s*-\s*[A-Z]{2,3}\/[A-Z]{2}\b` e `\bRG\s*(?:nº|n\.)?\s*[\d.X-]+\b` | `replace` -> `<NUMERO RG>` |
| `MATRICULA_SIAPE` | Termos matrícula ou siape | `(?i)\b(matr[íi]cula|siape)\b` (template lógico) | `replace` -> `***` |
| `TERMO_IDENTIDADE` | Palavras gatilho de identidade | `(?i)\b(RG|carteira|identidade|ssp)\b` | `replace` -> `***` |
| `ID_DOCUMENTO` | NB, IDs longos, CNJ, RNM, CRM | 6 regex: `NB...`, `\d{10,25}`, `ID...`, CNJ, RNM, CRM | `keep` |
| `ESTADO_CIVIL` | Estado civil (casado, solteira...) | Regex por termo: `(?i)\b{termo}\b` | `keep` |
| `ORGANIZACAO_CONHECIDA` | Órgãos/termos institucionais (INSS, TRF, etc.) | Regex por termo: `(?i)\b{termo}\b` | `keep` |
| `TERMO_COMUM` | Termos jurídicos comuns a preservar | `deny_list` de `termos_comuns.txt` | `keep` |
| `LEGAL_TITLE` | Títulos legais do arquivo `titulos_legais.txt` | Regex dinâmica: `(?i)\b({titulos})(?:\([A-Z]\))?\b` | `keep` |
| `SAFE_LOCATION` | Estados/capitais para não anonimizar | `deny_list` de `LISTA_ESTADOS_CAPITAIS_BR` | sem operador explícito -> cai em `DEFAULT` -> `keep` |
| `LEGAL_HEADER` | Cabeçalhos jurídicos para preservar | `deny_list` de `TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR` | sem operador explícito -> `DEFAULT` -> `keep` |
| `RG` | (se detectado por recognizer externo) | Sem regex custom no app | `replace` -> `***` |
| `LEGAL_OR_COMMON_TERM` | (placeholder no operador) | Sem recognizer custom no app | `keep` |
| `DEFAULT` | Fallback para entidade sem regra específica | N/A | `keep` |

**Observação importante de funcionamento**
Quando há sobreposição de detecções, o Presidio resolve por score/intervalo. Como `SAFE_LOCATION`, `LEGAL_HEADER`, `TERMO_COMUM`, `LEGAL_TITLE` têm score alto e ficam em `keep`, eles funcionam como escudo para evitar anonimização de termos jurídicos/locacionais que você quer preservar.
