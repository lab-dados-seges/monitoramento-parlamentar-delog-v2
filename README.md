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
   pip install -r requirements.txt
   ```

4. Execute o aplicativo:
   ```bash
   streamlit run app.py
   ```

O aplicativo estará disponível em `http://localhost:8501`.

## Estrutura do Projeto

```
monitoramento-parlamentar-delog-v2/
├── app.py                          # Ponto de entrada (streamlit run app.py)
├── src/                            # Código-fonte principal
│   ├── app.py                      # Lógica principal do Streamlit
│   ├── configuracao.py             # Constantes, colunas, labels e URLs
│   ├── analisador_legislativo.py   # Parser de referências legislativas
│   ├── enriquecedor.py             # Orquestrador bicameral
│   ├── pipeline.py                 # Pipeline de ETL (script executável)
│   ├── clientes/                   # Clientes de APIs externas
│   │   ├── base.py                 # Cliente HTTP base (retry + backoff)
│   │   ├── camara.py               # API da Câmara dos Deputados
│   │   └── senado.py               # API do Senado Federal
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
└── .gitignore
```

## Uso

### Executando o Aplicativo

```bash
streamlit run app.py
```

### Atualizando os Dados

Via script Python (recomendado):
```bash
python -m src.pipeline
```

Via notebook interativo:
```bash
jupyter notebook tratar_dados_v2.ipynb
```

## Automação

O projeto inclui automação via GitHub Actions que executa o pipeline diariamente às 06:01 (horário de Brasília).

- **Workflow**: `.github/workflows/update_data.yml`
- **Ação**: Executa o notebook via Papermill, commita e faz push das alterações

Para executar manualmente: acesse a aba "Actions" no GitHub e clique em "Run workflow".

## Dependências

| Biblioteca | Versão | Uso |
|---|---|---|
| Streamlit | 1.42.2 | Framework web do dashboard |
| Pandas | 2.2.3 | Manipulação de dados |
| Requests | 2.32.3 | Requisições HTTP para APIs |
| OpenPyXL | 3.1.5 | Leitura de arquivos Excel |

## Dados

### Fontes

- **CGNOR**: Dados internos da Coordenação-Geral de Normas
- **API Câmara**: https://dadosabertos.camara.leg.br/
- **API Senado**: https://legis.senado.leg.br/dadosabertos/

## Suporte

Para dúvidas ou problemas, entre em contato com a equipe do Núcleo de Inteligência de Dados - NID/SEGES/MGI.

## Licença

Este projeto é propriedade do Ministério da Gestão e da Inovação Pública (MGI) - SEGES.
