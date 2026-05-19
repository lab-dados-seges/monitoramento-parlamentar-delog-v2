# Monitoramento Parlamentar CGNOR/DELOG

## Descrição

Aplicativo web em Streamlit para monitoramento e acompanhamento de projetos de lei no Congresso Nacional Brasileiro. O sistema permite consultar proposições legislativas cadastradas pela Coordenação-Geral de Normas (CGNOR), obter informações detalhadas e acompanhar a tramitação na Câmara dos Deputados e no Senado Federal.

Link Principal: https://monitora-parlamentar-seges-v2.streamlit.app/

### Principais Funcionalidades

- **Consulta de Proposições**: Busca e exibição de projetos de lei com informações completas sobre tramitação, pareceres, emendas e substitutivos.
- **Integração com APIs Oficiais**: Dados atualizados diretamente das APIs da Câmara dos Deputados e do Senado Federal.
- **Controle Interno**: Acompanhamento de encaminhamentos, prazos e manifestações da SEGES/MGI.
- **Interface Interativa**: Dashboard intuitivo com filtros e visualizações detalhadas.
- **Exportação de Dados**: Possibilidade de exportar relatórios e dados processados.

## Instalação

### Pré-requisitos

- Python 3.11 ou superior
- Git
- (Opcional, apenas para executar o pipeline localmente) Credenciais de aplicação no Azure AD com acesso ao SharePoint da CGNOR

### Passos para Instalação

1. Clone o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd monitoramento-parlamentar-delog-v2
   ```

2. Crie um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows: .venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   # Para apenas executar o dashboard:
   pip install -r requirements.txt

   # Para executar o pipeline de ETL e/ou baixar a planilha do SharePoint:
   pip install -r requirements-dev.txt
   ```

4. (Apenas para o pipeline) Crie um arquivo `.env` na raiz com as credenciais Azure AD:
   ```
   AZURE_CLIENT_ID=...
   AZURE_CLIENT_SECRET=...
   AZURE_TENANT_ID=...
   ```

5. Execute o aplicativo:
   ```bash
   streamlit run app.py
   ```

O aplicativo estará disponível em `http://localhost:8501`.

## Estrutura do Projeto

```
monitoramento-parlamentar-delog-v2/
├── app.py                          # Ponto de entrada do dashboard (streamlit run app.py)
├── src/                            # Código-fonte principal
│   ├── configuracao.py             # Constantes, colunas, labels e URLs
│   ├── analisador_legislativo.py   # Parser de referências legislativas
│   ├── enriquecedor.py             # Orquestrador bicameral
│   ├── pipeline.py                 # Pipeline de ETL (script executável)
│   ├── clientes/                   # Clientes de APIs externas
│   │   ├── base.py                 # Cliente HTTP base (retry + backoff)
│   │   ├── camara.py               # API da Câmara dos Deputados
│   │   ├── senado.py               # API do Senado Federal
│   │   └── sharepoint.py           # Download da planilha via Microsoft Graph
│   └── componentes/                # Componentes de UI do Streamlit
│       ├── filtros.py              # Sidebar de filtros
│       ├── metricas.py             # Cards de métricas
│       ├── detalhes.py             # Abas de detalhamento
│       └── atualizacoes.py         # Últimas atualizações
├── data/
│   └── df_final_bicameral.csv      # Dados processados finais
├── image/
│   └── logo_verde_mgi.png
├── tratar_dados_v2.ipynb            # Notebook (orquestra o pipeline)
├── requirements.txt                 # Dependências de produção (versões fixas)
├── requirements-dev.txt             # Dependências de desenvolvimento e CI
├── .github/workflows/
│   └── update_data.yml              # Atualização diária via GitHub Actions
├── .devcontainer/
│   └── devcontainer.json            # Configuração do Dev Container
└── .gitignore
```

## Uso

### Executando o Aplicativo

```bash
streamlit run app.py
```

### Atualizando os Dados

**Baixar somente a planilha do SharePoint** (sem rodar o pipeline):
```bash
python -m src.clientes.sharepoint
```

**Rodar o pipeline ETL completo** usando a planilha já presente em `data/`:
```bash
python -m src.pipeline
```

**Baixar a planilha do SharePoint e rodar o pipeline** em sequência:
```bash
BAIXAR_DO_SHAREPOINT=1 python -m src.pipeline
```

**Via notebook interativo:**
```bash
jupyter notebook tratar_dados_v2.ipynb
```

> Os comandos que envolvem SharePoint exigem o `.env` configurado com as credenciais Azure AD descritas na seção de instalação.

## Automação

O projeto inclui automação via GitHub Actions que executa o pipeline diariamente às 06:01 (horário de Brasília).

- **Workflow**: `.github/workflows/update_data.yml`
- **Ação**: Em sequência, o workflow:
  1. Baixa a planilha mais recente do SharePoint via Microsoft Graph
  2. Executa o notebook `tratar_dados_v2.ipynb` via Papermill (gera o CSV bicameral)
  3. Commita o CSV atualizado e faz push de volta para a `main`

As credenciais do Azure AD ficam armazenadas como GitHub Secrets (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`).

Para executar manualmente: acesse a aba "Actions" no GitHub, selecione "Atualizar dados do monitoramento parlamentar" e clique em "Run workflow".

## Dependências

### Produção (`requirements.txt`)

| Biblioteca | Versão | Uso |
|---|---|---|
| Streamlit | 1.55.0 | Framework web do dashboard |
| Pandas | 2.2.3 | Manipulação de dados |
| Requests | 2.32.3 | Requisições HTTP para APIs |
| OpenPyXL | 3.1.5 | Leitura de arquivos Excel |

### Desenvolvimento e CI (`requirements-dev.txt`)

| Biblioteca | Versão | Uso |
|---|---|---|
| MSAL | 1.36.0 | Autenticação OAuth2 no Azure AD (SharePoint) |
| python-dotenv | 1.0.1 | Carregamento de variáveis do `.env` em dev local |
| Papermill | 2.6.0 | Execução do notebook no CI |
| Jupyter | 1.1.1 | Ambiente do notebook |
| nbconvert | 7.16.6 | Suporte ao Papermill |
| pytest | 8.3.4 | Suite de testes |
| pytest-mock | 3.14.0 | Mocks para os testes |

## Dados

### Fontes

- **CGNOR**: Planilha interna da Coordenação-Geral de Normas, armazenada no SharePoint corporativo e baixada automaticamente via Microsoft Graph.
- **API Câmara**: https://dadosabertos.camara.leg.br/
- **API Senado**: https://legis.senado.leg.br/dadosabertos/

### Fluxo de dados

```
Planilha CGNOR (SharePoint)
        ↓
src.clientes.sharepoint  →  data/ (planilha bruta)
        ↓
src.pipeline (carrega, extrai referências, enriquece via APIs, normaliza)
        ↓
data/df_final_bicameral.csv  →  consumido pelo app.py (Streamlit)
```

## Suporte

Para dúvidas ou problemas, entre em contato com a equipe do Núcleo de Inteligência de Dados - NID/SEGES/MGI.

## Licença

Este projeto é propriedade do Ministério da Gestão e da Inovação Pública (MGI) - SEGES.
