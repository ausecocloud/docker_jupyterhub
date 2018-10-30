FROM python:3.6-slim-stretch


# install requirements ... build packages are needed to install pycurl
RUN apt-get -y update \
 && apt-get -y upgrade \
 && apt-get -y install --no-install-recommends \
            curl \
 && apt-get -y install --no-install-recommends \
            gcc \
            libc6-dev \
            libcurl4-openssl-dev \
            libssl-dev \
 && pip3 install --upgrade --no-cache-dir \
         pip \
 && pip3 install --no-cache-dir \
         cryptography \
         pycurl \
 && apt-get -y purge \
            gcc \
            libc6-dev \
            libcurl4-openssl-dev \
            libssl-dev \
 && apt-get -y autoremove \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*


##########################################
#          https://github.com/ausecocloud/kubespawner/archive/ef5649f72b8ac431c0a43eda74d88e79d3e77137.zip \
#         jupyterhub-kubespawner==0.9.0 \
#         https://github.com/ausecocloud/kubespawner/archive/ef5649f72b8ac431c0a43eda74d88e79d3e77137.zip \
RUN pip3 install --no-cache-dir \
         jupyterhub==0.9.4 \
         oauthenticator==0.8.0 \
         psycopg2-binary \
         jupyterhub-kubespawner==0.9.0 \
         statsd \
         https://github.com/ausecocloud/keycloakauthenticator/archive/32e416c02eba8d7d3b39126865c8bde90afdaee0.zip \
 &&  curl -o /usr/local/bin/cull_idle_servers.py https://raw.githubusercontent.com/jupyterhub/jupyterhub/0.9.4/examples/cull-idle/cull_idle_servers.py

RUN mkdir -p /srv/jupyterhub/ \
 && mkdir -p /etc/jupyterhub \
 && addgroup --system jupyter \
 && adduser --system --ingroup jupyter jupyter \
 && chown jupyter:jupyter /srv/jupyterhub

COPY files/jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY files/ecocloud_logo.svg /srv/jupyterhub/ecocloud_logo.svg
COPY files/jupyterhub-config.yaml /etc/jupyterhub/jupyterhub-config.yaml
COPY files/ecocloud_hub_service.py /usr/local/bin/ecocloud_hub_service.py

WORKDIR /srv/jupyterhub/

USER jupyter

ENTRYPOINT ["jupyterhub"]
