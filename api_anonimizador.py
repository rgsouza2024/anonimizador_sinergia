# Nome do arquivo: api_anonimizador.py
# Objetivo: Expor o motor de anonimização como um Microserviço REST para consumo por outras linguagens (Node.js, C#, etc.)

import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from core.anonymizer_service import (
    executar_anonimizacao,
    analyzer_engine,
    anonymizer_engine,
)

app = FastAPI(
    title="Motor de Anonimização Sinergia API",
    description="Microserviço RESTful desacoplado para anonimização de textos e documentos jurídicos.",
    version="1.0.0",
)

# CORS habilitado para integração livre
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextoRequest(BaseModel):
    texto: str = Field(..., description="Texto original a ser anonimizado")
    nomes_metadados: Optional[List[str]] = Field(
        default_factory=list,
        description="Lista opcional de nomes para anonimização forçada",
    )


class AnonimizacaoResponse(BaseModel):
    texto_anonimizado: str
    entidades_detectadas: List[dict]
    tempo_processamento: float


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "analyzer_carregado": analyzer_engine is not None,
        "anonymizer_carregado": anonymizer_engine is not None,
    }


@app.post("/api/v1/anonimizar", response_model=AnonimizacaoResponse)
async def api_anonimizar(request: TextoRequest):
    try:
        inicio = time.time()
        nomes_set = set(request.nomes_metadados) if request.nomes_metadados else set()

        texto_anon, df_entidades, metricas = executar_anonimizacao(
            texto_original=request.texto,
            nomes_pf_metadados=nomes_set,
            retornar_metricas=True,
        )

        entidades = df_entidades.to_dict("records") if not df_entidades.empty else []
        tempo_processamento = round(time.time() - inicio, 3)

        return AnonimizacaoResponse(
            texto_anonimizado=texto_anon,
            entidades_detectadas=entidades,
            tempo_processamento=tempo_processamento,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Iniciando microserviço REST de anonimização na porta 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

