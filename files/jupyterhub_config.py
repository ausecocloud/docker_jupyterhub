# Configuration file for jupyterhub.

import glob
import os
import yaml

# -----------------------------------------------------------------------------
#  load configuration from yaml file and apply it to c
# -----------------------------------------------------------------------------
try:
    with open(os.environ.get('JUPYTERHUB_CONFIG_YAML',
                             '/etc/jupyterhub/jupyterhub-config.yaml')) as f:
        data = yaml.safe_load(f)
        for section in data:
            for key, value in data[section].items():
                c[section][key] = value

    if 'JUPYTERHUB_DB_URL' in os.environ:
        c.JupyterHub.db_url = os.environ['JUPYTERHUB_DB_URL']

except FileNotFoundError as e:
    # ignore file not found errors
    pass


extra_configs = sorted(glob.glob('/etc/jupyterhub/config/*.py'))
for ec in extra_configs:
    load_subconfig(ec)
