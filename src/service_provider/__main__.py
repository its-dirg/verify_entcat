from wsgiref.simple_server import make_server

from werkzeug.debug import DebuggedApplication
from werkzeug.wsgi import SharedDataMiddleware
from service_provider.wsgi import app

app.debug = True
app.secret_key = "abcdef"
app = DebuggedApplication(SharedDataMiddleware(app, {
    '/static': ('service_provider', 'site/static')
}))

print("Serving on port 8000...")
# app.run('', 8000, debug=True)
httpd = make_server('', 8000, app)
httpd.serve_forever()
