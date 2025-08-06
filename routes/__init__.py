from .idq_routes import idq_bp
from .montana_routes import montana_bp

def register_routes(app):
    app.register_blueprint(idq_bp, url_prefix="/api/idq")
    app.register_blueprint(montana_bp, url_prefix="/api/montana")