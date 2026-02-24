# Regressão de Anonimização

Este diretório guarda a base de regressão do motor de anonimização.

## Arquivos
- `cases.json`: casos de entrada (snippets reais anonimizados para teste).
- `baseline_snapshot.json`: saída de referência atual do motor.
- `run_baseline.py`: cria/verifica snapshot.

## Uso
1. Gerar snapshot inicial:
   `python tests/regression/run_baseline.py snapshot`
2. Verificar regressão após mudanças:
   `python tests/regression/run_baseline.py verify`

## Objetivo
Detectar mudanças não intencionais em:
- texto anonimizado final;
- entidades detectadas e respectivos trechos.
