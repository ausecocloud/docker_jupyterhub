# Copyright 2017 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.PHONY:	build push

PREFIX = hub.bccvl.org.au/jupyter
IMAGE = jupyterhub
TAG ?= 0.9.4
BUILD_OPTS ?=

IMAGE_ARG = $(PREFIX)/$(IMAGE):$(TAG)
PORT_ARGS = -p 8081:8081 -p 8010:8010 -p 8001:8001
ENV_ARGS = -e CONFIGPROXY_AUTH_TOKEN=test -e JUPYTERHUB_CRYPT_KEY=12345678901234567890123456789012


build:
	docker build $(BUILD_OPTS) -t $(PREFIX)/$(IMAGE):$(TAG) .

push:
	docker push $(PREFIX)/$(IMAGE):$(TAG)

run:
	# apt-get install npm vim
	# vim /etc/hosts
	# npm install -g configurable-http-proxy
	docker run --rm -it -v $(PWD):/code $(PORT_ARGS) $(ENV_ARGS) $(IMAGE_ARG) bash

test:
	docker run --rm -it $(PORT_ARGS) $(ENV_ARGS) $(IMAGE_ARG)

config:
	docker run --rm -it -v $(PWD):/code $(IMAGE_ARG) --generate-config --config /code/jupyterhub_config_gen.py
