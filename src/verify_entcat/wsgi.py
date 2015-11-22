import metadata_upload.wsgi
from werkzeug.wsgi import DispatcherMiddleware

from verify_entcat.service import app as verify_entcat

app = DispatcherMiddleware(verify_entcat, {
    "/upload_metadata": metadata_upload.wsgi.app
})
