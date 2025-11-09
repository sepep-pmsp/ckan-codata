import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model as model
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)


class CodataPlugin(plugins.SingletonPlugin):
    """
    Plugin para customizações do CKAN para o CODATA.
    Este plugin implementa diversas interfaces do CKAN para modificar o
    comportamento padrão, incluindo:
    - `IConfigurer`: Para adicionar diretórios de templates e recursos.
    - `IPackageController`: Para modificar metadados de datasets antes da indexação.
    - `ITemplateHelpers`: Para adicionar funções de ajuda aos templates.
    - `IFacets`: Para customizar as facetas de busca.
    """
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets)

    # --- IConfigurer ---
    def update_config(self, config_):
        """
        Adiciona os diretórios de templates e recursos públicos da extensão
        à configuração do CKAN.
        Isso permite a sobrescrita de templates e o uso de arquivos estáticos
        (CSS, JS, imagens) customizados.
        :param config_: Dicionário de configuração do CKAN.
        """
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "codata")

    # --- IPackageController ---
    def before_dataset_index(self, pkg_dict: dict) -> dict:
        """
        Modifica o dicionário de um dataset antes de ser indexado no Solr.
        Esta função extrai a 'spatial_granularity' dos recursos de um dataset
        e a adiciona como um campo no próprio dataset, permitindo que seja
        utilizada em facetas de busca.
        :param pkg_dict: Dicionário do dataset a ser indexado.
        :return: Dicionário do dataset modificado.
        """
        log.debug("--- DEBUG: Executando before_dataset_index para o dataset: %s ---", pkg_dict.get('name'))
        try:
            full_pkg_dict = toolkit.get_action('package_show')(
                data_dict={'id': pkg_dict['id']}
            )
            resources = full_pkg_dict.get('resources', [])
        except toolkit.ObjectNotFound:
            resources = []
            log.warning("Dataset %s não encontrado durante o before_dataset_index.", pkg_dict.get('id'))

        periodo_values = []
        for resource in resources:
            value = resource.get('spatial_granularity')
            if value and value not in periodo_values:
                periodo_values.append(value)

        if periodo_values:
            pkg_dict['spatial_granularity'] = periodo_values

        return pkg_dict

    # --- IFacets ---
    def dataset_facets(self, facets_dict, package_type):
        """
        Customiza os títulos das facetas na página de busca de datasets.
        :param facets_dict: Dicionário de facetas padrão.
        :param package_type: Tipo de pacote (geralmente 'dataset').
        :return: Dicionário de facetas customizado.
        """
        return {
            'organization': 'Organizações',
            'groups': 'Grupos',
            'tags': 'Etiquetas',
            'res_format': 'Formatos',
            'license_id': 'Licenças',
            'spatial_granularity': 'Granularidade Espacial'
        }

    def group_facets(self, facets_dict, group_type, package_type):
        """
        Customiza as facetas na página de um grupo específico.
        :param facets_dict: Dicionário de facetas padrão.
        :param group_type: Tipo de grupo.
        :param package_type: Tipo de pacote.
        :return: Dicionário de facetas customizado para grupos.
        """
        facets_dict.update({
            'organization': 'Organizações',
            'tags': 'Etiquetas',
            'res_format': 'Formatos',
            'license_id': 'Licenças',
            'spatial_granularity': 'Granularidade Espacial'
        })
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        """
        Customiza as facetas na página de uma organização específica.
        :param facets_dict: Dicionário de facetas padrão.
        :param organization_type: Tipo de organização.
        :param package_type: Tipo de pacote.
        :return: Dicionário de facetas customizado para organizações.
        """
        facets_dict.update({
            'groups': 'Grupos',
            'tags': 'Etiquetas',
            'res_format': 'Formatos',
            'license_id': 'Licenças',
            'spatial_granularity': 'Granularidade Espacial'
        })
        return facets_dict

    # --- ITemplateHelpers ---
    def get_helpers(self):
        """
        Registra funções de ajuda para serem usadas nos templates.
        :return: Dicionário mapeando nomes de helpers para suas funções.
        """
        return {
            'codata_total_resources': self._get_total_resources,
            'codata_total_datasets': self._get_total_datasets,
            'codata_total_storage_gb': self._get_total_storage_gb,
            'codata_weekly_updates': self._get_weekly_updates,
        }

    def _get_total_resources(self):
        """
        Calcula e retorna o número total de recursos públicos e ativos.
        :return: Número total de recursos.
        """
        try:
            query = model.Session.query(model.Resource).join(model.Package)\
                .filter(model.Package.state == 'active')\
                .filter(model.Package.private == False)\
                .filter(model.Resource.state == 'active')
            
            total_resources = query.count()
            return total_resources
        except Exception as e:
            log.error("Erro ao calcular o total de recursos: %s", e)
            return 0
    
    def _get_total_storage_gb(self):
        """
        Calcula e retorna o armazenamento total de todos os recursos em GB.
        :return: Armazenamento total em GB.
        """
        try:
            query = model.Session.query(func.sum(model.Resource.size))\
                .join(model.Package)\
                .filter(model.Package.state == 'active')\
                .filter(model.Package.private == False)\
                .filter(model.Resource.state == 'active')\
                .filter(model.Resource.size.isnot(None))
            
            total_bytes = query.scalar() or 0
            total_gb = round(total_bytes / (1024 * 1024 * 1024), 2)
            
            return total_gb
        except Exception as e:
            log.error("Erro ao calcular o armazenamento total: %s", e)
            return 0
    
    def _get_weekly_updates(self):
        """
        Calcula e retorna o número de recursos atualizados na última semana.
        :return: Número de recursos atualizados recentemente.
        """
        try:
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            
            query = model.Session.query(model.Resource)\
                .join(model.Package)\
                .filter(model.Package.state == 'active')\
                .filter(model.Package.private == False)\
                .filter(model.Resource.state == 'active')\
                .filter(model.Resource.last_modified >= one_week_ago)
            
            weekly_updates = query.count()
            return weekly_updates
        except Exception as e:
            log.error("Erro ao calcular as atualizações semanais: %s", e)
            return 0
    
    def _get_total_datasets(self):
        """
        Calcula e retorna o número total de datasets públicos e ativos.
        :return: Número total de datasets.
        """
        try:
            context = {'ignore_auth': True}
            data_dict = {
                'q': '*:*',
                'fq': '+dataset_type:dataset +state:active -private:true',
                'rows': 0
            }
            
            result = toolkit.get_action('package_search')(context, data_dict)
            return result.get('count', 0)
        except Exception as e:
            log.error("Erro ao calcular o total de datasets: %s", e)
            return 0