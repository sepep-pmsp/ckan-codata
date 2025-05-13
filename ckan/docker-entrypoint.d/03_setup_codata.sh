#!/usr/bin/env bash
set -e

echo "Installing ckanext-codata"
pip install -e /srv/app/src_extensions/ckanext-codata

echo "Adding ckanext-codata to CKAN__PLUGINS"
export CKAN__PLUGINS="$CKAN__PLUGINS codata"
