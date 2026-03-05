# Nome do arquivo: api_anonimizador.py
# Objetivo: Expor o motor de anonimização como um Microserviço REST para consumo por outras linguagens (Node.js, C#, etc.)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Reaproveitando sua lógica existente do app.py
from app import _anonimizar_logica

app = FastAPI(title="Motor de Anonimização Sinergia API")

class TextoRequest(BaseModel):
    texto: str
    nomes_metadados: Optional[List[str]] = []

class AnonimizacaoResponse(BaseModel):
    texto_anonimizado: str
    entidades_detectadas: List[dict] # Você pode tipar melhor isso se desejar
    tempo_processamento: float

@app.post("/api/v1/anonimizar", response_model=AnonimizacaoResponse)
async def api_anonimizar(request: TextoRequest):
    try:
        # Executa a pipeline que já definimos no app.py
        # _anonimizar_logica retorna (texto_anon, df_entidades) ou (texto_anon, df, metricas)
        resultado = _anonimizar_logica(
            texto_original=request.texto,
            nomes_pf_metadados=set(request.nomes_metadados),
            retornar_metricas=True
        )
        
        texto_anon, df_entidades, metricas = resultado
        
        return AnonimizacaoResponse(
            texto_anonimizado=texto_anon,
            entidades_detectadas=df_entidades.to_dict('records'),
            tempo_processamento=metricas.get("tempo_segundos", 0) if isinstance(metricas, dict) else 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Rodar a API na porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
