import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class CodataPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    

    # IConfigurer
    #NOTE: update_config is the interface for the plugin config
    def update_config(self, config_):
        #a toolkit function to tell CKAN where are the plugin view templates
        toolkit.add_template_directory(config_, "templates")
        #a toolkit function to tell CKAN where are the plugin public assets such as JS, CSS, and images.
        toolkit.add_public_directory(config_, "public")
        #a toolkit function that helps us to add assets libraries for our plugin. We use this to create our WebAssets for CSS and JS assets.
        toolkit.add_resource("assets", "codata")
        
        
        
        