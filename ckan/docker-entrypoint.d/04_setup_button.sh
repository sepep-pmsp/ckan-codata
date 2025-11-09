echo "Forcing ckan.uploads_enabled = true"
ckan config-tool $CKAN_INI "ckan.uploads_enabled = true"

echo "Forcing ckan.storage_path = /var/lib/ckan"
ckan config-tool $CKAN_INI "ckan.storage_path = /var/lib/ckan"

echo "Forcing ckan.requests.timeout = 300"
ckan config-tool $CKAN_INI "ckan.requests.timeout = 300"

echo "Forcing ckan.requests.timeout = 300"
ckan config-tool $CKAN_INI "ckan.locale_default = pt_BR"