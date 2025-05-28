#!/bin/bash

ckan config-tool $CKAN_INI "scheming.dataset_schemas = ckanext.scheming:ckan_dataset_schema.yaml"
ckan config-tool $CKAN_INI "scheming.presets = ckanext.scheming:presets.json"
ckan config-tool $CKAN_INI "search.facets = organization groups tags res_format license_id res_extras_spatial_coverage"
ckan config-tool $CKAN_INI "ckan.extra_resource_fields = spatial_coverage"




