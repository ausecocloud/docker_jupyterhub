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


class OptionsHandler(HubAuthenticated, RequestHandler):
    # hub_users can be a set of users who are allowed to access the service
    # `getuser()` here would mean only the user who started the service
    # can access the service:

    # hub_users = {getuser()}

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

    @authenticated
    def get(self):
        try:
            options = yaml.safe_load(open(self.settings['profiles'], 'r'))
        except Exception as e:
            app_log.error('Could not read profiles: %s', e)
            options = {}
        ret = {
            'profile_list': [
                {
                    'display_name': opt['display_name'],
                    'description': opt['description']
                } for opt in options.get('profile_list', [])
            ]
        }
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
