from wsgiref.simple_server import make_server

from werkzeug.debug import DebuggedApplication
from werkzeug.wsgi import SharedDataMiddleware

from verify_entcat.wsgi import app

app.debug = True
app.secret_key = "abcdef"
app = DebuggedApplication(SharedDataMiddleware(app, {
    '/static': ('verify_entcat', 'site/static')
}))

print("Serving on port 8000...")
httpd = make_server('', 8000, app)
httpd.serve_forever()
