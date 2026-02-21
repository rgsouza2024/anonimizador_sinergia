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

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

**Mapa entidade por entidade (motor atual em `app.py`)**

ReferÃªncia principal: `app.py:66`, `app.py:152`, `app.py:243`.

| Entidade | O que detecta | Regex/lista usada | Output final |
|---|---|---|---|
| `PERSON` | Nomes de pessoas (NER + sobrenomes frequentes) | Regex dinÃ¢mica por sobrenome: `(?i)\b{sobrenome}\b` + recognizer spaCy | `replace` -> `<NOME>` |
| `LOCATION` | LocalizaÃ§Ãµes (spaCy NER) | Sem regex no app (recognizer padrÃ£o) | `replace` -> `<ENDERECO>` |
| `EMAIL_ADDRESS` | E-mails | Sem regex no app (recognizer padrÃ£o Presidio) | `replace` -> `<EMAIL>` |
| `PHONE_NUMBER` | Telefones | Sem regex no app (recognizer padrÃ£o Presidio) | `mask` -> mascara 4 chars finais com `*` |
| `DATE_TIME` | Datas/horÃ¡rios | Sem regex no app (recognizer padrÃ£o Presidio) | `keep` |
| `CPF` | CPF formatado | `\b\d{3}\.\d{3}\.\d{3}-\d{2}\b` | `replace` -> `<CPF>` |
| `OAB_NUMBER` | NÃºmero OAB (com/sem prefixo) | `\b(?:OAB\s+)?\d{1,6}(?:\.\d{3})?\s*\/\s*[A-Z]{2}\b` | `replace` -> `<OAB>` |
| `CEP_NUMBER` | CEP com/sem pontuaÃ§Ã£o | `\b(\d{5}-?\d{3}|\d{2}\.\d{3}-?\d{3})\b` | `replace` -> `<CEP>` |
| `CNH` | CNH formatada ou 11 dÃ­gitos isolados | `\bCNH\s*(?:nÂº|n\.)?\s*\d{11}\b` e `\b(?<![\w])\d{11}(?![\w])\b` | `replace` -> `***********` |
| `SIAPE` | SIAPE formatado ou 7 dÃ­gitos isolados | `\bSIAPE\s*(?:nÂº|n\.)?\s*\d{7}\b` e `\b(?<![\w])\d{7}(?![\w])\b` | `replace` -> `***` |
| `CI` | Carteira de identidade (CI) | `\bCI\s*(?:nÂº|n\.)?\s*[\d.]{7,11}-?\d\b` e `\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b` | `replace` -> `***` |
| `CIN` | Carteira de identidade nacional (CIN) | `\bCIN\s*(?:nÂº|n\.)?\s*[\d.]{7,11}-?\d\b` e `\b\d{1,2}\.?\d{3}\.?\d{3}-?\d\b` | `replace` -> `***` |
| `RG_NUMBER` | RG com prefixo/formato completo ou simples | `\bRG\s*(?:nÂº|n\.)?\s*[\d.X-]+(?:-\dÂª\s*VIA)?\s*-\s*[A-Z]{2,3}\/[A-Z]{2}\b` e `\bRG\s*(?:nÂº|n\.)?\s*[\d.X-]+\b` | `replace` -> `<NUMERO RG>` |
| `MATRICULA_SIAPE` | Termos matrÃ­cula ou siape | `(?i)\b(matr[Ã­i]cula|siape)\b` (template lÃ³gico) | `replace` -> `***` |
| `TERMO_IDENTIDADE` | Palavras gatilho de identidade | `(?i)\b(RG|carteira|identidade|ssp)\b` | `replace` -> `***` |
| `ID_DOCUMENTO` | NB, IDs longos, CNJ, RNM, CRM | 6 regex: `NB...`, `\d{10,25}`, `ID...`, CNJ, RNM, CRM | `keep` |
| `ESTADO_CIVIL` | Estado civil (casado, solteira...) | Regex por termo: `(?i)\b{termo}\b` | `keep` |
| `ORGANIZACAO_CONHECIDA` | Ã“rgÃ£os/termos institucionais (INSS, TRF, etc.) | Regex por termo: `(?i)\b{termo}\b` | `keep` |
| `TERMO_COMUM` | Termos jurÃ­dicos comuns a preservar | `deny_list` de `termos_comuns.txt` | `keep` |
| `LEGAL_TITLE` | TÃ­tulos legais do arquivo `titulos_legais.txt` | Regex dinÃ¢mica: `(?i)\b({titulos})(?:\([A-Z]\))?\b` | `keep` |
| `SAFE_LOCATION` | Estados/capitais para nÃ£o anonimizar | `deny_list` de `LISTA_ESTADOS_CAPITAIS_BR` | sem operador explÃ­cito -> cai em `DEFAULT` -> `keep` |
| `LEGAL_HEADER` | CabeÃ§alhos jurÃ­dicos para preservar | `deny_list` de `TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR` | sem operador explÃ­cito -> `DEFAULT` -> `keep` |
| `RG` | (se detectado por recognizer externo) | Sem regex custom no app | `replace` -> `***` |
| `LEGAL_OR_COMMON_TERM` | (placeholder no operador) | Sem recognizer custom no app | `keep` |
| `DEFAULT` | Fallback para entidade sem regra especÃ­fica | N/A | `keep` |

**ObservaÃ§Ã£o importante de funcionamento**
Quando hÃ¡ sobreposiÃ§Ã£o de detecÃ§Ãµes, o Presidio resolve por score/intervalo. Como `SAFE_LOCATION`, `LEGAL_HEADER`, `TERMO_COMUM`, `LEGAL_TITLE` tÃªm score alto e ficam em `keep`, eles funcionam como escudo para evitar anonimizaÃ§Ã£o de termos jurÃ­dicos/locacionais que vocÃª quer preservar.
