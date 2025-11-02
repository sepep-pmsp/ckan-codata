import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model as model
from sqlalchemy import func
from datetime import datetime, timedelta

class CodataPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets)  


    # IConfigurer
    #NOTE: update_config is the interface for the plugin config
    def update_config(self, config_):
        #a toolkit function to tell CKAN where are the plugin view templates
        toolkit.add_template_directory(config_, "templates")
        #a toolkit function to tell CKAN where are the plugin public assets such as JS, CSS, and images.
        toolkit.add_public_directory(config_, "public")
        #a toolkit function that helps us to add assets libraries for our plugin. We use this to create our WebAssets for CSS and JS assets.
        toolkit.add_resource("assets", "codata")
        

    # IPackageController hook: before_dataset_index
    def before_dataset_index(self, pkg_dict: dict) -> dict:
        spatial_values = []
        for resource in pkg_dict.get('resources', []):
            value = resource.get('spatial_granularity')
            if value and value not in spatial_values:
                spatial_values.append(value)
        if spatial_values:
            pkg_dict['res_extras_spatial_granularity'] = spatial_values
        return pkg_dict
    

    def dataset_facets(self, facets_dict, package_type):
        """Define títulos de facets nativamente no CKAN"""
        return {
            'organization': 'Organizações',
            'groups': 'Grupos',
            'tags': 'Etiquetas',
            'res_format': 'Formatos',
            'license_id': 'Licenças',
            'res_extras_spatial_granularity': 'Granularidade Espacial'
        }
    
    
    def get_helpers(self):
        return {
            'codata_total_resources': self._get_total_resources,
            'codata_total_datasets': self._get_total_datasets,
       #     'codata_total_downloads': self._get_total_downloads,
            'codata_total_storage_gb': self._get_total_storage_gb,
            'codata_weekly_updates': self._get_weekly_updates,
        }

    def _get_total_resources(self):
        """
        Retorna a quantidade total de recursos públicos no portal
        """
        try:
            # Query para contar recursos de datasets públicos
            query = model.Session.query(model.Resource).join(model.Package)\
                .filter(model.Package.state == 'active')\
                .filter(model.Package.private == False)\
                .filter(model.Resource.state == 'active')
            
            total_resources = query.count()
            return total_resources
        except Exception as e:
            # Log do erro e retorna 0 como fallback
            toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
            return 0
    
    def _get_total_storage_gb(self):
        """
        Retorna o total de armazenamento em GB
        """
        try:
            # Query para somar o tamanho de todos os recursos
            query = model.Session.query(func.sum(model.Resource.size))\
                .join(model.Package)\
                .filter(model.Package.state == 'active')\
                .filter(model.Package.private == False)\
                .filter(model.Resource.state == 'active')\
                .filter(model.Resource.size.isnot(None))
            
            total_bytes = query.scalar() or 0
            
            # Converter bytes para GB
            total_gb = round(total_bytes / (1024 * 1024 * 1024), 2)
            
            return total_gb
        except Exception as e:
            return 0
    
    def _get_weekly_updates(self):
        """
        Retorna a quantidade de atualizações de recursos na última semana
        """
        try:
            # Calcular a data de uma semana atrás
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Query para contar recursos modificados na última semana usando apenas last_modified
            query = model.Session.query(model.Resource)\
                .join(model.Package)\
                .filter(model.Package.state == 'active')\
                .filter(model.Package.private == False)\
                .filter(model.Resource.state == 'active')\
                .filter(model.Resource.last_modified >= one_week_ago)
            
            weekly_updates = query.count()
            return weekly_updates
        except Exception as e:
            return 0
    
    def _get_total_datasets(self):
        """
        Retorna a quantidade total de datasets públicos
        """
        try:
            # Usando a API do CKAN para buscar datasets
            context = {'ignore_auth': True}
            data_dict = {
                'q': '*:*',
                'fq': '+dataset_type:dataset +state:active -private:true',
                'rows': 0  # Só queremos o count, não os dados
            }
            
            result = toolkit.get_action('package_search')(context, data_dict)
            return result.get('count', 0)
        except Exception as e:
            return 0