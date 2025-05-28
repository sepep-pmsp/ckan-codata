#!/usr/bin/env python
# test_custom_indexer.py

from ckanext.codata.plugin import CodataPlugin

# Instantiate your plugin (note that SingletonPlugin classes may be stateless)
plugin = CodataPlugin()

# Create a dummy dataset dictionary with resources having extras for spatial_coverage
dummy_dataset = {
    'resources': [
        {
            'extras': [
                {'key': 'spatial_coverage', 'value': 'Europe'},
                {'key': 'spatial_coverage', 'value': 'Asia'}
            ]
        },
        {
            'extras': [
                {'key': 'spatial_coverage', 'value': 'Europe'}  # Duplicate, should be filtered out
            ]
        }
    ]
}

# Call the before_dataset_index hook to simulate indexing
modified_dataset = plugin.before_dataset_index(dummy_dataset)

print("Modified dataset index dict:")
print(modified_dataset)

