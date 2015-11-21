from wsgiref.simple_server import make_server

from werkzeug.debug import DebuggedApplication
from werkzeug.wsgi import SharedDataMiddleware

from verify_entcat.wsgi import app as verify_entcat

verify_entcat.app.debug = True
verify_entcat.app.secret_key = "abcdef"
verify_entcat.app.wsgi_app = DebuggedApplication(SharedDataMiddleware(verify_entcat.app.wsgi_app, {
    '/static': ('verify_entcat', 'site/static')
}))

print("Serving on port 8000...")
httpd = make_server('', 9000, verify_entcat)
httpd.serve_forever()
