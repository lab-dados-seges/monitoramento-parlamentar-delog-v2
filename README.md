# Monitoramento Parlamentar CGNOR/DELOG

## Descrição

Este projeto é um aplicativo web desenvolvido em Streamlit para monitoramento e acompanhamento de projetos de lei no Congresso Nacional Brasileiro. O sistema permite consultar proposições legislativas previamente cadastradas pela Coordenação-Geral de Normas (CGNOR), obter informações detalhadas e acompanhar a tramitação tanto na Câmara dos Deputados quanto no Senado Federal.

Link Principal: https://monitora-parlamentar-seges-v2.streamlit.app/

### Principais Funcionalidades

- **Consulta de Proposições**: Busca e exibição de projetos de lei com informações completas sobre tramitação, pareceres, emendas e substitutivos.
- **Integração com APIs Oficiais**: Dados atualizados diretamente das APIs da Câmara dos Deputados e do Senado Federal.
- **Controle Interno**: Acompanhamento de encaminhamentos, prazos e manifestações da SEGES/MGI.
- **Interface Interativa**: Dashboard intuitivo com filtros e visualizações detalhadas.
- **Exportação de Dados**: Possibilidade de exportar relatórios e dados processados.

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Git (opcional, para clonagem do repositório)

### Passos para Instalação

1. Clone o repositório (se aplicável) ou baixe os arquivos do projeto:
   ```bash
   git clone <url-do-repositorio>
   cd monitoramento-parlamentar-delog-v2
   ```

2. Crie um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute o aplicativo:
   ```bash
   streamlit run home_v2.py
   ```

O aplicativo estará disponível em `http://localhost:8501`.

## Uso

### Executando o Aplicativo

Após a instalação, execute o comando acima. O dashboard principal exibirá:

- Lista de projetos de lei monitorados
- Filtros por origem, status e datas
- Detalhes completos de cada proposição
- Links para documentos oficiais

### Processamento de Dados

Para atualizar ou processar novos dados, utilize o notebook `tratar_dados_v2.ipynb`:

1. Abra o notebook no Jupyter:
   ```bash
   jupyter notebook tratar_dados_v2.ipynb
   ```

2. Execute as células em ordem para:
   - Carregar dados brutos
   - Processar referências legislativas
   - Enriquecer dados com APIs da Câmara e Senado
   - Gerar o arquivo final `data/df_final_bicameral.csv`

### Automação de Atualização

O projeto inclui uma automação via GitHub Actions que executa o processamento de dados automaticamente todos os dias às 06:01 (horário de Brasília).

- **Arquivo de Workflow**: `.github/workflows/update_data.yml`
- **Ferramentas Utilizadas**: Papermill para execução do notebook, Git para versionamento
- **Ações**:
  - Execução diária agendada
  - Atualização automática do arquivo `data/df_final_bicameral.csv`
  - Commit e push das alterações se houverem dados novos

Para executar manualmente ou testar:
1. Acesse a aba "Actions" no repositório GitHub
2. Selecione o workflow "Atualizar dados do monitoramento parlamentar"
3. Clique em "Run workflow"

## Estrutura do Projeto

```
monitoramento-parlamentar-delog-v2/
├── home_v2.py                 # Aplicativo principal Streamlit
├── tratar_dados_v2.ipynb      # Notebook para processamento de dados
├── requirements.txt           # Dependências Python
├── README.md                  # Este arquivo
├── data/
│   └── df_final_bicameral.csv # Dados processados finais
└── image/
    ├── logo_mgi.png
    └── logo_verde_mgi.png     # Logos utilizados no aplicativo
```

### Arquivos Principais

- **`home_v2.py`**: Contém a lógica do dashboard Streamlit, configurações de colunas, labels e interface do usuário.
- **`tratar_dados_v2.ipynb`**: Notebook Jupyter responsável por:
  - Parsing de referências legislativas
  - Integração com APIs da Câmara e Senado
  - Enriquecimento de dados bicamerais
  - Geração do dataset final

## Dependências

As principais bibliotecas utilizadas são:

- **Streamlit** (>=1.37): Framework para criação da interface web
- **Pandas** (>=2.2): Manipulação e análise de dados
- **Requests** (>=2.32): Requisições HTTP para APIs
- **OpenPyXL** (>=3.1): Leitura/escrita de arquivos Excel

Para instalar todas as dependências:
```bash
pip install -r requirements.txt
```

## Dados

### Fonte de Dados

- **CGNOR**: Dados internos da Coordenação-Geral de Normas
- **API Câmara dos Deputados**: https://dadosabertos.camara.leg.br/
- **API Senado Federal**: https://legis.senado.leg.br/dadosabertos/

### Estrutura dos Dados

O arquivo `data/df_final_bicameral.csv` contém colunas organizadas por:

- **Identificação**: Projeto de Lei, Origem, Regex
- **Câmara dos Deputados**: ID, Projeto, Ementa, Datas, Tramitação, Pareceres, Links
- **Senado Federal**: ID, Projeto, Ementa, Datas, Tramitação, Pareceres, Links
- **Controle Interno**: Encaminhamentos, Prazos, Manifestações SEGES

## Desenvolvimento

### Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Testes

Para executar testes (se implementados):
```bash
pytest
```

### Linting

Para verificar qualidade do código:
```bash
flake8 .
```

## Suporte

Para dúvidas ou problemas, entre em contato com a equipe do Núcleo de Inteligencia de dados - NID/SEGES/MGI.

## Licença

Este projeto é propriedade do Ministério da Gestão e da Inovação Pública (MGI) - SEGES.
