# Urbis CKAN

## Sumário

- [Como Contribuir](#como-contribuir)
- [Visão Geral do Projeto](#visão-geral-do-projeto)
- [Principais Funcionalidades e Customizações](#principais-funcionalidades-e-customizações)
- [Extensões Adicionais](#extensões-adicionais)
- [Deploy e CI/CD](#deploy-e-cicd)
- [Política de Backup](#política-de-backup)

## Como Contribuir

Contribuições para melhorar este portal são bem-vindas. Para configurar o ambiente de desenvolvimento e entender o fluxo de trabalho, consulte nosso [**Guia de Contribuição**](CONTRIBUTING.md).

## Visão Geral do Projeto

Este repositório contém o código-fonte e a configuração da instância customizada do CKAN para o projeto CODATA. O projeto utiliza uma extensão personalizada, a `ckanext-codata`, para adaptar as funcionalidades da plataforma, com foco principal na customização de metadados e na integração de estatísticas do portal.

## Principais Funcionalidades e Customizações

As customizações estão concentradas na extensão `ckanext-codata`, que implementa lógicas de backend através do `plugin.py` e personaliza a interface do usuário com templates e arquivos estáticos.

### Funcionalidades do Plugin (`plugin.py`)

O arquivo `plugin.py` é o núcleo da extensão e implementa diversas interfaces do CKAN:

*   **`IConfigurer`**: Registra os diretórios customizados da extensão (`templates/`, `public/`, `assets/`), permitindo que a extensão sobrescreva templates padrão e sirva arquivos estáticos próprios (CSS, imagens, etc.).

*   **`IPackageController`**: Modifica o processo de indexação de dados. Através do método `before_dataset_index`, ele extrai o metadado `spatial_granularity` de cada recurso e o "promove" ao nível do dataset. Isso torna o campo "Granularidade Espacial" uma faceta pesquisável.

*   **`IFacets`**: Substitui os nomes técnicos das facetas de busca por títulos mais amigáveis, como "Organizações" e "Granularidade Espacial", melhorando a experiência de busca.

*   **`ITemplateHelpers`**: Implementa funções Python que podem ser chamadas diretamente dos templates para exibir informações dinâmicas.

### Funções de Template (Helpers)

Estas funções são expostas para serem usadas nos templates (`.html`) para exibir estatísticas sobre o portal:

*   **`_get_total_resources()`**: Retorna a quantidade total de recursos públicos no portal.
*   **`_get_total_datasets()`**: Retorna a quantidade total de datasets públicos.
*   **`_get_total_storage_gb()`**: Retorna o total de armazenamento de todos os recursos em Gigabytes.
*   **`_get_weekly_updates()`**: Retorna a quantidade de recursos atualizados na última semana.

### Indexação de Metadados (`before_dataset_index`)

Esta função é a customização de backend mais importante para a busca. O CKAN, por padrão, não permite filtrar datasets por metadados que existem apenas no nível do *recurso*.

A função **`before_dataset_index`** resolve isso:
1.  **Inspeciona o Dataset**: Acessa cada um dos recursos dentro do dataset que será indexado.
2.  **Coleta os Valores**: Lê o valor do campo `spatial_granularity` de cada recurso.
3.  **Promove os Dados**: Agrupa os valores únicos encontrados e os adiciona a uma nova lista no nível do *dataset*.
4.  **Habilita a Faceta**: Ao "promover" essa informação, o campo `spatial_granularity` se torna visível para o motor de busca (Solr), que consegue então criar um filtro (faceta) a partir dele.

## Extensões Adicionais

Além da `ckanext-codata`, esta instância do CKAN utiliza outras extensões importantes:

*   **`ckanext-scheming`**: Permite a criação de esquemas de metadados personalizados através de arquivos YAML. É usada para definir o campo `spatial_granularity` no formulário de recursos.
*   **`ckanext-envvars`**: Permite que a configuração do CKAN seja lida a partir de variáveis de ambiente, o que é essencial para ambientes containerizados.
*   **`ckanext-pdf_view`**: Integra um visualizador de PDFs diretamente na página do recurso.
*   **`ckanext-geoview`**: Adiciona a capacidade de visualizar dados geoespaciais (como GeoJSON) em mapas interativos.

## Deploy e CI/CD

O processo de deploy da aplicação é automatizado com GitHub Actions, definido no arquivo `.github/workflows/deploy_ckan.yml`.

### Gatilhos do Workflow

O processo é iniciado automaticamente em um `push` para a branch `master` ou pode ser acionado manualmente.

### Processo de Build e Push (Job: `build_push_acs`)

1.  **Login no Azure Container Registry (ACR):** Autentica-se no registro de container.
2.  **Build e Push das Imagens:** O workflow constrói as imagens Docker para `nginx`, `postgresql` e `ckan` e as envia para o ACR com a tag `latest`.

### Processo de Deploy (Job: `deploy_to_vm`)

1.  **SSH na VM:** Conecta-se à máquina virtual de produção.
2.  **Atualização do Repositório:** Executa `git pull` para sincronizar com a branch `master`.
3.  **Pull das Imagens:** Baixa as imagens mais recentes do ACR com `docker compose -f docker-compose.prod.yml pull`.
4.  **Reinício dos Serviços:** Reinicia os serviços com as novas imagens usando `docker compose -f docker-compose.prod.yml up -d`.

## Política de Backup

A política de backup automatizado garante a recuperabilidade dos bancos de dados da plataforma.

### Componentes do Backup

O backup inclui dumps dos bancos de dados `ckandb` (metadados gerais) e `datastore` (dados tabulares). **Não inclui** os arquivos do *filestore* (uploads de usuários).

### Processo de Execução

1.  **Criação dos Dumps**: O script usa `pg_dump` para exportar os bancos de dados.
2.  **Compactação**: Os dumps são combinados em um arquivo `.tar.gz`.
3.  **Armazenamento**: O arquivo é enviado para um contêiner no Azure Blob Storage.
4.  **Retenção**: Apenas os 4 backups mais recentes são mantidos; os mais antigos são excluídos.
5.  **Logs**: Todas as operações são registradas em `/var/log/ckan_backup.log` na VM.
