import json
import os
from urllib.parse import urlparse
import yaml

from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.log import app_log
from tornado.options import define, options, parse_command_line
from tornado.web import RequestHandler, Application, authenticated

from jupyterhub.services.auth import HubAuthenticated


from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2 import InvalidGrantError, TokenExpiredError
from requests_oauthlib import OAuth2Session


class Keycloak(object):
    # TODO: would be nice if this was async as well

    def __init__(self, baseurl, realm, client_id, client_secret):
        self.token_url = '{baseurl}/realms/{realm}/protocol/openid-connect/token'.format(
            baseurl=baseurl, realm=realm,
        )
        adminurl = '{baseurl}/admin/realms/{realm}'.format(
            baseurl=baseurl, realm=realm
        )
        self.user_url = '{adminurl}/users/{userid}'.format(adminurl=adminurl, userid='{userid}')
        self.client_url = '{adminurl}/clients?clientId={clientid}'.format(adminurl=adminurl, clientid='{clientid}')

        self.client_id = client_id
        self.client_secret = client_secret
        self.client_uuid = None

        client = BackendApplicationClient(client_id)
        self.session = OAuth2Session(
            client=client,
            scope=['openid'],  # , 'email', 'profile', 'offline_access'
            auto_refresh_url=self.token_url,
            auto_refresh_kwargs={
                'client_id': client_id,
                'client_secret': client_secret
            },
            token_updater=lambda tok: None
        )
        self._fetch_token()
        self._fetch_client_uuid()

    def _fetch_token(self):
        # get initital token
        self.session.fetch_token(
            self.token_url,
            client_id=self.client_id, client_secret=self.client_secret,
            scope=self.session.scope
        )

    def _fetch_client_uuid(self):
        client_url = self.client_url.format(clientid=self.client_id)
        res = self.session.get(client_url)
        res.raise_for_status()
        self.client_uuid = res.json()[0]['id']

    def get_client_role_mappings(self, userid):
        # 1. get client uuid
        user_url = self.user_url.format(userid=userid) + '/role-mappings/clients/' + self.client_uuid + '/composite'
        res = self.session.get(user_url)
        res.raise_for_status()
        return res.json()


class OptionsHandler(HubAuthenticated, RequestHandler):
    # hub_users can be a set of users who are allowed to access the service
    # `getuser()` here would mean only the user who started the service
    # can access the service:

    # hub_users = {getuser()}

    _keycloak = None

    # set CORS headers
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "Authorization")

    # CORS preflight
    def options(self):
        # no body
        self.set_status(204)
        self.finish()

    @property
    def keycloak(self):
        if not self._keycloak:
            try:
                self._keycloak = Keycloak(
                    os.environ['KEYCLOAK_BASE_URL'],
                    os.environ['KEYCLOAK_REALM'],
                    os.environ['OAUTH_CLIENT_ID'],
                    os.environ['OAUTH_CLIENT_SECRET']
                )
            except Exception as e:
                app_log.error('Unable to connect to Keycloak: %s', e)
        return self._keycloak

    def get_user_roles(self, userid):
        client_roles = []
        try:
            # app_log.info('Retrieve roles for user %s', userid)
            client_roles = [
                role['name'] for role in
                self.keycloak.get_client_role_mappings(userid)
            ]
            # app_log.info('Roles: %s', client_roles)
        except Exception as e:
            app_log.error('Failed to retrieve user roles from Keycloak: %s', e)
        return client_roles

    @authenticated
    def get(self):
        user = self.hub_auth.get_user(self)
        roles = self.get_user_roles(user['name'])

        try:
            options = yaml.safe_load(open(self.settings['profiles'], 'r'))
        except Exception as e:
            app_log.error('Could not read profiles: %s', e)
            options = {}
        ret = {
            'profile_list': [
                {
                    'id': opt['id'],
                    'display_name': opt['display_name'],
                    'description': opt['description'],
                    'default': opt['default'],
                } for opt in options.get('profile_list', [])
            ]
        }
        if 'flavours' in roles:
            ret['flavour_list'] = [
                {
                    'id': opt['id'],
                    'display_name': opt['display_name'],
                    'description': opt['description'],
                    'default': opt['default'],
                } for opt in options.get('flavour_list')
            ]
        self.set_header('content-type', 'application/json')
        self.write(json.dumps(ret))


def main():
    define(
        'profiles',
        default='/etc/jupyterhub/config/profiles.yaml',
        help="Path to profiles config file",
    )
    define(
        'listen_url',
        default='http://0.0.0.0:10100',
        help="The inteface and port this service should listen on.")
    # enable default cli parser (logging options and --help)
    parse_command_line()
    # env:
    #   JUPYTERHUB_SERVICE_NAME
    #.  JUPYTERHUB_SERVICE_URL.   ... the url configured in jupyterhub service config
    #.  JUPYTERUHB_SERVICE_PREFIX ... always ends in /
    #.  JUPYTERHUB_API_TOKEN
    #.  JUPYTERHUB_CLIENT_ID
    #.  JUPYTERHUB_OAUTH_CALLBACK_URL
    #.  JUPYTERHUB_API_URL
    #.  JUPYTERHUB_BASE_URL

    app = Application(
        [
            (os.environ['JUPYTERHUB_SERVICE_PREFIX'] + 'profile_list', OptionsHandler),
            # (r'.*', OptionsHandler)
        ],
        # settings
        profiles=options.profiles,
    )

    http_server = HTTPServer(app)
    url = urlparse(options.listen_url)

    http_server.listen(url.port, url.hostname)

    IOLoop.current().start()


if __name__ == '__main__':
    main()
