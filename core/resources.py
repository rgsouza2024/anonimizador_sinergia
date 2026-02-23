"""Resource loading and static domain lists for the anonymization engine."""

from pathlib import Path

from core.config import (
    NOME_ARQUIVO_SOBRENOMES,
    NOME_ARQUIVO_TERMOS_COMUNS,
    NOME_ARQUIVO_TITULOS,
)

def carregar_lista_de_arquivo(nome_arquivo):
    lista_itens = []
    caminho_base = Path(__file__).resolve().parents[1]
    caminho_arquivo = caminho_base / nome_arquivo
    try:
        with caminho_arquivo.open("r", encoding="utf-8") as f:
            for linha in f:
                item = linha.strip()
                if item:
                    lista_itens.append(item)
    except FileNotFoundError:
        print(f"AVISO: Arquivo de lista '{nome_arquivo}' não encontrado.")
    except Exception as e:
        print(f"ERRO: Erro ao ler o arquivo '{nome_arquivo}': {e}")
    return lista_itens

LISTA_NOMES_COMUNS = carregar_lista_de_arquivo(NOME_ARQUIVO_SOBRENOMES)
# Alias de compatibilidade para chamadas existentes do app.
LISTA_SOBRENOMES_FREQUENTES_BR = LISTA_NOMES_COMUNS
LISTA_TERMOS_COMUNS = carregar_lista_de_arquivo(NOME_ARQUIVO_TERMOS_COMUNS)
LISTA_TITULOS_LEGAIS = carregar_lista_de_arquivo(NOME_ARQUIVO_TITULOS)
LISTA_ESTADOS_CAPITAIS_BR = ["Acre", "AC", "Alagoas", "AL", "Amapá", "AP", "Amazonas", "AM", "Bahia", "BA", "Ceará", "CE", "Distrito Federal", "DF", "Espírito Santo", "ES", "Goiás", "GO", "Maranhão", "MA", "Mato Grosso", "MT", "Mato Grosso do Sul", "MS", "Minas Gerais", "MG", "Pará", "PA", "Paraíba", "PB", "Paraná", "PR", "Pernambuco", "PE", "Piauí", "PI", "Rio de Janeiro", "RJ", "Rio Grande do Norte", "RN", "Rio Grande do Sul", "RS", "Rondônia", "RO", "Roraima", "RR", "Santa Catarina", "SC", "São Paulo", "SP", "Sergipe", "SE", "Tocantins", "TO",
                             "Aracaju", "Belém", "Belo Horizonte", "Boa Vista", "Brasília", "Campo Grande", "Cuiabá", "Curitiba", "Florianópolis", "Fortaleza", "Goiânia", "João Pessoa", "Macapá", "Maceió", "Manaus", "Natal", "Palmas", "Porto Alegre", "Porto Velho", "Recife", "Rio Branco", "Salvador", "São Luís", "Teresina", "Vitória"]
TERMOS_CABECALHO_LEGAL_NAO_ANONIMIZAR = ["EXMO. SR. DR. JUIZ FEDERAL", "EXMO SR DR JUIZ FEDERAL", "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ FEDERAL", "JUIZ FEDERAL", "EXMO. SR. DR. JUIZ DE DIREITO", "EXMO SR DR JUIZ DE DIREITO", "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO", "JUIZ DE DIREITO", "JUIZADO ESPECIAL FEDERAL", "VARA DA SEÇÃO JUDICIÁRIA", "SEÇÃO JUDICIÁRIA", "EXMO.", "EXMO", "SR.", "DR.", "Dra.", "DRA.", "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) FEDERAL",
                                       "EXCELENTÍSSIMO", "Senhor", "Doutor", "Senhora", "Doutora", "EXCELENTÍSSIMA", "EXCELENTÍSSIMO(A)", "Senhor(a)", "Doutor(a)", "Juiz", "Juíza", "Juiz(a)", "Juiz(íza)", "Assunto", "Assuntos"]
LISTA_ESTADO_CIVIL = ["casado", "casada", "solteiro", "solteira", "viúvo", "viúva", "divorciado", "divorciada",
                      "separado", "separada", "unido", "unida", "companheiro", "companheira", "amasiado", "amasiada", "união estável", "em união estável"]
LISTA_ORGANIZACOES_CONHECIDAS = ["FUNASA", "INSS", "IBAMA", "CNPQ", "IBGE", "FIOCRUZ", "SERPRO", "DATAPREV", "VALOR", "Justiça", "Justica", "Segredo", "PJe", "Assunto", "Tribunal Regional Federal", "Assuntos", "Vara Federal", "Vara", "Justiça Federal", "Federal", "Juizado", "Especial", "Federal", "Vara Federal de Juizado Especial Cível", "Turma",
                                "Turma Recursal", "PJE", "SJGO", "SJDF", "SJMA", "SJAC", "SJAL", "SJAP", "SJAM", "SJBA", "SJCE", "SJDF", "SJES", "SJGO", "SJMA", "SJMG", "SJMS", "SJMT", "SJPA", "SJPB", "SJPE", "SJPI", "SJPR", "SJPE", "SJRN", "SJRO", "SJRR", "SJRS", "SJSC", "SJSE", "SJSP", "SJTO", "Justiça Federal da 1ª Região", "PJe - Processo Judicial Eletrônico"]
