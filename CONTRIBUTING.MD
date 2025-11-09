# Contribuindo com Customizações de Metadados e Plugins no CKAN

Este guia explica como contribuir com o desenvolvimento da extensão `ckanext-codata`, com foco na customização de metadados, indexação e criação de facetas de busca no ambiente de desenvolvimento do CKAN.

## Sumário

- [Sobre o CKAN](#sobre-o-ckan)
- [Pré-requisitos](#pré-requisitos)
- [Configuração do Ambiente de Desenvolvimento](#configuração-do-ambiente-de-desenvolvimento)
- [Desenvolvendo Plugins e Customizando Metadados](#desenvolvendo-plugins-e-customizando-metadados)
  - [Passo 1: Definindo o Campo no Esquema de Metadados](#passo-1-definindo-o-campo-no-esquema-de-metadados)
  - [Passo 2: Tornando o Metadado Pesquisável (Indexação)](#passo-2-tornando-o-metadado-pesquisável-indexação)
  - [Passo 3: Exibindo o Campo como Filtro (Faceta)](#passo-3-exibindo-o-campo-como-filtro-faceta)
- [Customização da Interface (Opcional)](#customização-da-interface-opcional)
- [Workflow de Desenvolvimento](#workflow-de-desenvolvimento)
- [Troubleshooting](#troubleshooting)
- [Contribuindo](#contribuindo)
- [Estrutura de Arquivos e Diretórios](#estrutura-de-arquivos-e-diretórios)
- [Referências e Documentação](#referências-e-documentação)


## Sobre o CKAN

CKAN (Comprehensive Knowledge Archive Network) é uma plataforma open-source para gerenciamento de dados que permite organizações publicar, compartilhar e gerenciar dados de forma estruturada. Sua arquitetura modular permite extensibilidade através de plugins (extensões), que podem adicionar funcionalidades personalizadas, modificar a interface do usuário, integrar APIs externas ou implementar workflows específicos de dados.

## Pré-requisitos

- Docker e Docker Compose instalados
- Git instalado
- Conhecimentos básicos de Python, Jinja2 e Docker.

## Configuração do Ambiente de Desenvolvimento

### 1. Clonando o Repositório

```bash
# Clone o repositório principal
git clone https://github.com/basedosdados/ckan-codata.git
cd ckan-codata
```

### 2. Configuração do Ambiente

Copie o arquivo de configuração de desenvolvimento. Ele contém as variáveis de ambiente necessárias para executar o CKAN em modo de desenvolvimento.

```bash
# Copie o arquivo de configuração
cp .env.example .env
```

### 3. Build e Execução dos Containers

Com o Docker, o ambiente de desenvolvimento é containerizado, garantindo consistência e facilidade de configuração.

```bash
# Construa as imagens de desenvolvimento e inicie os serviços
docker compose up --build -d

# Verifique se todos os containers estão rodando
docker compose ps
```

A extensão `ckanext-codata` (localizada em `src/`) é montada como um volume no container. Isso permite que alterações no código sejam refletidas em tempo real, exigindo apenas o reinício do serviço para alterações em Python.

## Desenvolvendo Plugins e Customizando Metadados

Este projeto utiliza a extensão `ckanext-scheming` para definir esquemas de metadados e a `ckanext-codata` para implementar lógicas customizadas. O foco é enriquecer os metadados e torná-los funcionais na plataforma.

O exemplo abaixo demonstra como o campo **"Granularidade Espacial"** foi implementado.

### Passo 1: Definindo o Campo no Esquema de Metadados

A customização começa pela definição do campo no esquema de metadados, utilizando `ckanext-scheming`. O arquivo `ckan/ckan_dataset_schema.yaml` é o local para essas definições.

Adicionamos `spatial_granularity` à seção `resource_fields`:

```yaml
# Em ckan/ckan_dataset_schema.yaml

resource_fields:
  # ... outros campos de recurso
  
  - field_name: spatial_granularity
    label: Granularidade Espacial
    form_placeholder: Ex: País, Estado, Município
    choices:
      - value: pais
        label: País
      - value: estado
        label: Estado
      - value: municipio
        label: Município
```

- **`field_name`**: O nome interno do campo.
- **`label`**: O rótulo exibido no formulário.
- **`choices`**: Define uma lista de opções pré-definidas, criando um campo de seleção.

Com essa definição, o campo "Granularidade Espacial" aparecerá no formulário de edição de cada recurso.

### Passo 2: Tornando o Metadado Pesquisável (Indexação)

Por padrão, metadados de *recursos* não são pesquisáveis na busca principal de *datasets*. Para habilitar a busca, usamos a interface `IPackageController` no nosso plugin `ckanext-codata`.

O método `before_dataset_index` é executado antes de um dataset ser indexado no Solr. Nós o utilizamos para "promover" o valor do campo `spatial_granularity` do nível do recurso para o nível do dataset.

```python
# Em src/ckanext-codata/ckanext/codata/plugin.py

class CodataPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IPackageController, inherit=True) 

    def before_dataset_index(self, pkg_dict: dict) -> dict:
        """
        Coleta os valores do campo 'spatial_granularity' de todos os recursos
        e os adiciona ao dicionário principal do dataset para indexação no Solr.
        """
        try:
            full_pkg_dict = toolkit.get_action('package_show')(
                data_dict={'id': pkg_dict['id']}
            )
            resources = full_pkg_dict.get('resources', [])
        except toolkit.ObjectNotFound:
            resources = []

        # Coleta os valores únicos do campo
        granularity_values = []
        for resource in resources:
            value = resource.get('spatial_granularity')
            if value and value not in granularity_values:
                granularity_values.append(value)
        
        # Adiciona a lista de valores ao campo do dataset que será indexado
        if granularity_values:
            pkg_dict['spatial_granularity'] = granularity_values
        
        return pkg_dict
```

Agora, o Solr irá indexar cada dataset com uma lista das "Granularidades Espaciais" de seus recursos.

### Passo 3: Exibindo o Campo como Filtro (Faceta)

Após a indexação, podemos usar o campo como um filtro (faceta) na barra lateral da página de busca. Para isso, implementamos a interface `IFacets`.

```python
# Em src/ckanext-codata/ckanext/codata/plugin.py

class CodataPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IFacets)

    def dataset_facets(self, facets_dict, package_type):
        """
        Adiciona e renomeia facetas na página de busca.
        """
        return {
            'organization': 'Organizações',
            'groups': 'Grupos',
            'tags': 'Etiquetas',
            'res_format': 'Formatos',
            'license_id': 'Licenças',
            'spatial_granularity': 'Granularidade Espacial' # Nossa nova faceta
        }
```

Com isso, "Granularidade Espacial" aparecerá como uma opção de filtro na interface, permitindo que os usuários refinem a busca de datasets com base neste metadado.

## Customização da Interface (Opcional)

Embora o foco seja em metadados, a `ckanext-codata` também permite customizações de UI.

- **CSS**: Altere `src/ckanext-codata/ckanext/codata/public/custom.css` para sobrescrever estilos.
- **Templates**: Modifique arquivos em `src/ckanext-codata/ckanext/codata/templates/` para alterar a estrutura HTML das páginas. Use `{% ckan_extends %}` para herdar de templates padrão.
- **Recursos Estáticos**: Imagens e outros arquivos podem ser adicionados em `src/ckanext-codata/ckanext/codata/public/`.

As alterações são registradas no `plugin.py` através da interface `IConfigurer`:

```python
# Em src/ckanext-codata/ckanext/codata/plugin.py
def update_config(self, config_):
    toolkit.add_template_directory(config_, "templates")
    toolkit.add_public_directory(config_, "public")
    toolkit.add_resource("assets", "codata")
```

## Workflow de Desenvolvimento

1.  **Desenvolvimento Local**: Faça suas alterações nos arquivos da extensão em `src/ckanext-codata`.
2.  **Aplicando Mudanças**:
    - Para alterações em Python (`plugin.py`), reinicie o container: `docker compose restart ckan`.
    - Para CSS, templates e arquivos estáticos, apenas recarregue a página no navegador.
3.  **Testes**: Acesse a instância local do CKAN em `http://localhost:5000` para verificar suas alterações.

## Troubleshooting

- **CSS não carrega**: Verifique se o recurso foi registrado no `plugin.py` e limpe o cache do navegador (Ctrl+F5).
- **Templates não atualizam**: Confirme que `{% ckan_extends %}` está presente e que o caminho do arquivo está correto.
- **Mudanças no plugin não funcionam**: Reinicie o container `ckan` e verifique os logs com `docker compose logs ckan`.

## Contribuindo

1.  Faça um fork do repositório.
2.  Crie uma branch para sua feature (`git checkout -b feature/minha-feature`).
3.  Faça commit de suas alterações (`git commit -m "feat: Descreve a nova feature"`).
4.  Envie para a sua branch (`git push origin feature/minha-feature`).
5.  Abra um Pull Request no repositório principal.

## Estrutura de Arquivos e Diretórios

Este documento descreve a estrutura de arquivos e diretórios do projeto `ckan-codata`, explicando a finalidade de cada componente principal.

### Visão Geral

O projeto é organizado em uma estrutura de monorepo, contendo a configuração do Docker para orquestração dos serviços e o código-fonte da extensão CKAN customizada.

```
ckan-codata/
├── .env.example              # Exemplo de arquivo de variáveis de ambiente para desenvolvimento
├── .gitignore                # Arquivos e diretórios ignorados pelo Git
├── docker-compose.prod.yml   # Configuração do Docker Compose para produção
├── docker-compose.yml        # Configuração do Docker Compose para desenvolvimento
├── README.md                 # Documentação principal do projeto
├── CONTRIBUTING.md           # Guia de contribuição focado em metadados
├── bin/                      # Scripts de utilidade para gerenciamento do ambiente
├── ckan/                     # Configurações e schemas específicos da instância CKAN
│   ├── ckan_dataset_schema.yaml # Definição do esquema de metadados (usado por ckanext-scheming)
│   ├── Dockerfile              # Dockerfile para a imagem de produção do CKAN
│   ├── Dockerfile.dev          # Dockerfile para a imagem de desenvolvimento do CKAN
│   └── setup/                  # Scripts de inicialização e configuração do CKAN
├── nginx/                    # Configuração do Nginx (proxy reverso)
├── postgresql/               # Configuração do banco de dados PostgreSQL
└── src/                      # Diretório contendo o código-fonte das extensões customizadas
    └── ckanext-codata/         # Extensão principal do projeto
        ├── ckanext/
        │   └── codata/
        │       ├── __init__.py
        │       ├── plugin.py       # Lógica principal da extensão (interfaces do CKAN)
        │       ├── assets/         # Arquivos CSS/JS gerenciados por webassets
        │       ├── public/         # Arquivos estáticos (imagens, CSS, etc.)
        │       └── templates/      # Templates Jinja2 para sobrescrever a UI do CKAN
        └── setup.py                # Script de instalação da extensão
```

### Componentes Principais

#### `docker-compose.yml` e `docker-compose.prod.yml`

- **`docker-compose.yml`**: Orquestra os serviços necessários para o ambiente de desenvolvimento (CKAN, PostgreSQL, Solr, Redis). Monta o código-fonte local como volume para permitir o desenvolvimento em tempo real.
- **`docker-compose.prod.yml`**: Configuração otimizada para produção, utilizando imagens mais enxutas e configurações de segurança apropriadas.

#### `ckan/`

Este diretório centraliza as configurações da aplicação CKAN.
- **`ckan_dataset_schema.yaml`**: Arquivo fundamental para a customização de metadados. Ele é lido pela extensão `ckanext-scheming` para definir os campos, tipos e validações dos formulários de datasets e recursos.
- **`Dockerfile.dev`**: Utilizado pelo `docker-compose.yml`, este Dockerfile instala as dependências de desenvolvimento e configura o CKAN para recarregar automaticamente (hot-reloading) quando alterações são feitas.
- **`setup/`**: Contém scripts que são executados na inicialização do container para configurar a instância, como a ativação de extensões e a aplicação de configurações.

#### `src/ckanext-codata/`

Este é o coração do projeto, a extensão customizada do CKAN.
- **`plugin.py`**: Arquivo mais importante da extensão. É aqui que as [interfaces do CKAN](https://docs.ckan.org/en/2.9/plugins/interfaces.html) são implementadas para modificar o comportamento padrão da plataforma. Exemplos:
  - `IConfigurer`: Para adicionar diretórios de templates e recursos.
  - `IPackageController`: Para interceptar e modificar dados de datasets antes de serem indexados.
  - `IFacets`: Para customizar os filtros de busca (facetas).
  - `ITemplateHelpers`: Para adicionar funções utilitárias aos templates.
- **`templates/`**: Contém arquivos de template `.html` (Jinja2) que sobrescrevem os templates padrão do CKAN, permitindo a customização da interface.
- **`public/`**: Para arquivos estáticos como CSS, imagens e fontes que são servidos diretamente pelo servidor web.
- **`assets/`**: Para arquivos CSS e JavaScript que são processados e minificados através do sistema de `webassets` do CKAN.

#### `bin/`

Scripts de conveniência para interagir com o ambiente Docker, como `reload` (reinicia o serviço do CKAN) e `shell` (acessa o terminal do container CKAN).

## Referências e Documentação

- [CKAN Theming Guide](https://docs.ckan.org/en/latest/theming/index.html)
- [CKAN Plugin Interfaces](https://docs.ckan.org/en/latest/plugins/interfaces.html)
- [ckanext-scheming](https://github.com/ckan/ckanext-scheming)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/en/3.0.x/templates/)
