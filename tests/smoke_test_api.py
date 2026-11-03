"""Smoke test para api_anonimizador.py."""

import sys
from pathlib import Path
from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import api_anonimizador
from api_anonimizador import app

client = TestClient(app)


def test_smoke():
    print("\n" + "=" * 60)
    print("INICIANDO SMOKE TEST DA API (api_anonimizador.py)")
    print("=" * 60)

    # 1. Teste de Health Check
    print("\n[1/5] Testando GET /health...")
    resp_health = client.get("/health")
    assert resp_health.status_code == 200, f"Falha no healthcheck: {resp_health.status_code}"
    health_data = resp_health.json()
    print(f"  -> Status: {resp_health.status_code}")
    print(f"  -> Resposta: {health_data}")
    assert health_data["status"] == "ok"
    assert health_data["analyzer_carregado"] is True
    assert health_data["anonymizer_carregado"] is True
    print("  [OK] Healthcheck passou com sucesso!")

    # 2. Teste de Anonimização Simples
    print("\n[2/5] Testando POST /api/v1/anonimizar com texto simples...")
    payload_1 = {
        "texto": "O reclamante Carlos Eduardo Souza, portador do CPF 123.456.789-00, reside na Rua das Palmeiras, 450."
    }
    resp_anon = client.post("/api/v1/anonimizar", json=payload_1)
    assert resp_anon.status_code == 200, f"Erro na requisição: {resp_anon.text}"
    data_1 = resp_anon.json()
    print(f"  -> Status: {resp_anon.status_code}")
    print(f"  -> Texto original: {payload_1['texto']}")
    print(f"  -> Texto anonimizado: {data_1['texto_anonimizado']}")
    print(f"  -> Entidades encontradas: {len(data_1['entidades_detectadas'])}")
    print(f"  -> Tempo de processamento: {data_1['tempo_processamento']}s")

    assert "<CPF/CIN>" in data_1["texto_anonimizado"] or "123.456.789-00" not in data_1["texto_anonimizado"]
    assert "123.456.789-00" not in data_1["texto_anonimizado"], "CPF não foi anonimizado!"
    assert data_1["tempo_processamento"] >= 0
    assert len(data_1["entidades_detectadas"]) > 0
    print("  [OK] Anonimização de texto básico passou com sucesso!")

    # 3. Teste com nomes nos metadados
    print("\n[3/5] Testando POST /api/v1/anonimizar com 'nomes_metadados'...")
    payload_2 = {
        "texto": "Notifique-se Roberto Alencar de Lima sobre a decisão da 1ª Vara Federal.",
        "nomes_metadados": ["Roberto Alencar de Lima"]
    }
    resp_meta = client.post("/api/v1/anonimizar", json=payload_2)
    assert resp_meta.status_code == 200, f"Erro: {resp_meta.text}"
    data_2 = resp_meta.json()
    print(f"  -> Status: {resp_meta.status_code}")
    print(f"  -> Texto anonimizado: {data_2['texto_anonimizado']}")
    assert "Roberto Alencar de Lima" not in data_2["texto_anonimizado"]
    print("  [OK] Anonimização forçada por metadados passou com sucesso!")

    # 3b. Revisão humana: nomes escritos à mão e trechos que não devem ser tarjados
    print("\n[3b/5] Testando 'nomes_manuais' e 'nao_tarjar'...")
    payload_revisao = {
        "texto": "O Ministro SCHIETTI votou. O autor João Lima, CPF 926.511.422-72, citou Lima (2017).",
        "nomes_manuais": ["Schietti"],
        "nao_tarjar": ["Lima", "926.511.422-72"],
    }
    resp_revisao = client.post("/api/v1/anonimizar", json=payload_revisao)
    assert resp_revisao.status_code == 200, f"Erro: {resp_revisao.text}"
    texto_revisao = resp_revisao.json()["texto_anonimizado"]
    print(f"  -> Texto anonimizado: {texto_revisao}")
    assert "SCHIETTI" not in texto_revisao, "Nome manual não foi tarjado!"
    assert "João" not in texto_revisao, "O nome ao lado do trecho liberado ficou à mostra!"
    assert texto_revisao.count("Lima") == 2, "Trecho marcado como 'nao_tarjar' foi tarjado!"
    assert "926.511.422-72" in texto_revisao, "CPF marcado como 'nao_tarjar' foi tarjado!"
    print("  [OK] Revisão humana (nomes_manuais e nao_tarjar) passou com sucesso!")

    # 4. Teste de validação de erro (payload inválido)
    print("\n[4/5] Testando validação de entrada inválida...")
    resp_invalid = client.post("/api/v1/anonimizar", json={"campo_errado": 123})
    assert resp_invalid.status_code == 422, f"Esperava 422, obteve {resp_invalid.status_code}"
    print(f"  -> Status esperado retornado: {resp_invalid.status_code}")
    print("  [OK] Validação de esquema Pydantic funcionou perfeitamente!")

    # 5. Healthcheck deve falhar (503) quando um motor não carregou
    print("\n[5/5] Testando GET /health com motor ausente...")
    analyzer_original = api_anonimizador.analyzer_engine
    api_anonimizador.analyzer_engine = None
    try:
        resp_falha = client.get("/health")
    finally:
        api_anonimizador.analyzer_engine = analyzer_original
    assert resp_falha.status_code == 503, f"Esperava 503, obteve {resp_falha.status_code}"
    assert resp_falha.json()["status"] == "erro"
    assert resp_falha.json()["analyzer_carregado"] is False
    print(f"  -> Status esperado retornado: {resp_falha.status_code}")
    print("  [OK] Healthcheck sinaliza falha do motor corretamente!")

    print("\n" + "=" * 60)
    print("TODOS OS TESTES DO SMOKE TEST PASSARAM COM SUCESSO!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_smoke()
