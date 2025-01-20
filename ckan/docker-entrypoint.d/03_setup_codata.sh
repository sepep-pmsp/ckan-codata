#!/usr/bin/env bash
set -e

echo "Installing ckanext-codata"
pip install -e /srv/app/src_extensions/ckanext-codata

echo "Installing ckanext-codata"
export CKAN__PLUGINS="$CKAN__PLUGINS codata"


