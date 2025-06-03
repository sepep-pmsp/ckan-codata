import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model as model
from sqlalchemy import func

class CodataPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)  


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
            value = resource.get('spatial_coverage')
            if value and value not in spatial_values:
                spatial_values.append(value)
        if spatial_values:
            pkg_dict['res_extras_spatial_coverage'] = spatial_values
        return pkg_dict
    
    def after_dataset_search(self, search_results: dict, search_params: dict) -> dict:
    # Suppose you want to inject a custom mapping into the search_results
        search_results['facet_titles'] = {
            'organization': 'Organizações',
            'groups': 'Grupos',
            'tags': 'Etiquetas',
            'res_format': 'Formatos',
            'license_id': 'Licenças',
            'res_extras_spatial_coverage': 'Cobertra Espacial'
        }
        return search_results


    def get_helpers(self):
        return {
            'codata_total_resources': self._get_total_resources,
       #     'codata_total_datasets': self._get_total_datasets,
       #     'codata_total_downloads': self._get_total_downloads,
       #     'codata_total_storage_gb': self._get_total_storage_gb,
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