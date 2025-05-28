import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class CodataPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)


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



