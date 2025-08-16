# Anonimizador SINERGIA - TRF1

<p align="center">
  <img src="Logo Projeto Sinergia TRF1 - Fundo Transparente.png" alt="Logo Projeto Sinergia" width="200">
</p>

## 📋 Sobre o Projeto

O **Anonimizador SINERGIA** é uma ferramenta desenvolvida pelo Projeto Sinergia do Tribunal Regional Federal da 1ª Região (TRF1) para anonimização automática de documentos jurídicos e administrativos. A aplicação utiliza tecnologia de Processamento de Linguagem Natural (NLP) para identificar e anonimizar informações sensíveis, mantendo a integridade e o contexto jurídico dos documentos.

A ferramenta é especialmente útil para:
- Proteger dados pessoais em documentos judiciais
- Atender a requisitos de sigilo e privacidade
- Facilitar a publicação de documentos em ambientes públicos
- Garantir a conformidade com a LGPD (Lei Geral de Proteção de Dados)

## 🚀 Funcionalidades

### Interface Intuitiva
A aplicação oferece uma interface web amigável com duas principais funcionalidades:

1. **Anonimização de Texto Colado**
   - Cole ou digite diretamente o texto a ser anonimizado
   - Visualização imediata do resultado
   - Download do documento anonimizado em formato .docx
   - Visualização das entidades detectadas

2. **Anonimização de Arquivos PDF**
   - Upload de documentos PDF
   - Extração e anonimização automática do conteúdo
   - Comparação do texto original e anonimizado
   - Download do resultado em formato .docx

## 🎯 Tipos de Entidades Anonimizadas

O sistema identifica e trata automaticamente diversos tipos de informações sensíveis:

### Dados Pessoais
- **Nomes Próprios**: Substituídos por `<NOME>`
- **Endereços**: Substituídos por `<ENDERECO>`
- **E-mails**: Substituídos por `<EMAIL>`
- **Telefones**: Parcialmente mascarados com `****`

### Documentos de Identificação
- **CPF**: Substituídos por `<CPF>`
- **OAB**: Substituídos por `<OAB>`
- **CEP**: Substituídos por `<CEP>`
- **CNH**: Substituídos por `***`
- **RG**: Substituídos por `***`
- **SIAPE**: Substituídos por `***`
- **CI/CIN**: Substituídos por `***`

### Identificadores Específicos
- **Números de Benefício (NB)**
- **IDs do PJe**
- **Número de processo CNJ**
- **Matrículas SIAPE**

## 📚 Bases de Dados Customizadas

O anonimizador utiliza bases de dados especializadas para melhor reconhecimento de entidades jurídicas:

### Sobrenomes Comuns Brasileiros
Arquivo `sobrenomes_comuns.txt` contendo mais de 2.800 sobrenomes frequentes no Brasil, permitindo uma identificação mais precisa de nomes próprios.

### Termos Jurídicos Comuns
Arquivo `termos_comuns.txt` com mais de 3.000 termos jurídicos e administrativos que **não devem ser anonimizados**, como:
- Termos legais ("EXMO. SR. DR. JUIZ FEDERAL")
- Estados civis ("casado", "solteira", etc.)
- Organizações conhecidas (INSS, FUNASA, etc.)
- Termos técnicos jurídicos

## 🛠️ Tecnologias Utilizadas

### Core
- **Python 3.x**: Linguagem principal da aplicação
- **Microsoft Presidio**: Engine principal de anonimização
- **spaCy**: Processamento de linguagem natural (modelo `pt_core_news_lg`)
- **Gradio**: Interface web intuitiva

### Manipulação de Documentos
- **PyMuPDF (fitz)**: Extração de texto de PDFs
- **python-docx**: Geração de arquivos .docx
- **pandas**: Manipulação de dados e resultados

### Gerenciamento
- **python-dotenv**: Gerenciamento de variáveis de ambiente
- **pip**: Gerenciamento de dependências

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)
- Modelo de linguagem spaCy para português

### Passo a passo

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/anonimizador_sinergia.git
cd anonimizador_sinergia
```

2. **Crie um ambiente virtual (recomendado):**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Instale o modelo de linguagem spaCy para português:**
```bash
python -m spacy download pt_core_news_lg
```

5. **Execute a aplicação:**
```bash
python anonimizador_trf1_logo.py
```

6. **Acesse a interface web:**
Abra seu navegador e acesse `http://localhost:7860` (ou o endereço indicado no terminal)

## ⚙️ Configuração

### Variáveis de Ambiente
O projeto suporta configuração via arquivo `.env` para personalizações futuras:
```env
# Exemplo de variáveis de ambiente (opcional)
DEBUG=true
PORT=7860
```

### Personalização de Listas
Você pode personalizar as listas de:
- Sobrenomes em `sobrenomes_comuns.txt`
- Termos jurídicos em `termos_comuns.txt`

## 📖 Uso

### Anonimização de Texto
1. Acesse a aba "⌨️ Anonimizar Texto Colado"
2. Cole ou digite o texto desejado na área apropriada
3. Clique em "🔍 Anonimizar Texto"
4. O resultado aparecerá na área de "Texto Anonimizado"
5. Clique em "📊 Ver Entidades Detectadas" para ver o que foi identificado
6. Faça download do documento anonimizado usando o botão de download

### Anonimização de PDF
1. Acesse a aba "🗂️ Anonimizar Arquivo PDF"
2. Clique em "Selecione o arquivo PDF" e escolha seu documento
3. Clique em "🔍 Anonimizar PDF Carregado"
4. Após o processamento, você poderá:
   - Ver o texto original extraído
   - Ver o texto anonimizado
   - Baixar o documento anonimizado em .docx

## 🔧 Desenvolvimento

### Estrutura do Projeto
```
anonimizador_sinergia/
├── anonimizador_trf1_logo.py    # Aplicação principal
├── sobrenomes_comuns.txt        # Lista de sobrenomes brasileiros
├── termos_comuns.txt            # Termos jurídicos protegidos
├── requirements.txt             # Dependências do projeto
├── .gitignore                   # Arquivos ignorados pelo Git
└── README.md                    # Documentação
```

### Principais Componentes

#### Motor de Análise (`analyzer_engine`)
Responsável por identificar entidades sensíveis no texto utilizando:
- Reconhecimento automático de padrões (CPF, CNH, etc.)
- Lista negra de sobrenomes comuns
- Lista negra de termos jurídicos protegidos

#### Motor de Anonimização (`anonymizer_engine`)
Aplica as regras de anonimização às entidades identificadas:
- Substituição por placeholders
- Mascaramento parcial
- Preservação de termos protegidos

### Personalização de Regras

Você pode ajustar as regras de anonimização modificando a função `obter_operadores_anonimizacao()`:

```python
def obter_operadores_anonimizacao():
    return {
        "DEFAULT": OperatorConfig("keep"),
        "PERSON": OperatorConfig("replace", {"new_value": "<NOME>"}),
        "LOCATION": OperatorConfig("replace", {"new_value": "<ENDERECO>"}),
        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
        "PHONE_NUMBER": OperatorConfig("mask", {
            "type": "mask", 
            "masking_char": "*", 
            "chars_to_mask": 4, 
            "from_end": True
        }),
        # ... outras regras
    }
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

Projeto Sinergia - TRF1
- Website: [TRF1](https://www.trf1.jus.br)

## 🙏 Agradecimentos

- Microsoft Presidio Team
- spaCy Community
- Gradio Team
- Comunidade de código aberto

## 📚 Referências

- [Microsoft Presidio Documentation](https://microsoft.github.io/presidio/)
- [spaCy Portuguese Model](https://spacy.io/models/pt)
- [Gradio Documentation](https://gradio.app/docs/)