import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class LiverpoolPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceView)


    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'liverpool')

    def info(self):
        return {
            "name": "gdoc_view",
            "title": toolkit._('Google Doc View'),
            "icon": "compass",
            "always_available": True,
        }

    def setup_template_variables(self, context, data_dict):
        return {
            "url": data_dict["resource"]["url"]
        }

    def can_view(self, data_dict):
        return data_dict['resource']['format'].lower() in ['doc', 'pdf', 'xls', 'xlsx']

    def view_template(self, context, data_dict):
        return "gdoc_preview.html"

    def form_template(self, context, data_dict):
        return "gdoc_form.html"