
import traceback
from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
load_dotenv()

from app.config import get_config
from extensions import db, migrate
import os, logging, json, time, uuid, sys
from .routes import bp


def create_app(config_overrides = None):
    app = Flask(__name__)
    
    app.config.from_object(get_config())
    
    if config_overrides:
        if isinstance(config_overrides, dict):
            app.config.update(config_overrides)
        else:
            app.config.from_object(config_overrides)
        
        
    level = app.config.get("LOG_LEVEL", logging.INFO)
    level_name = os.getenv("LOG_LEVEL")
    if level_name:
        level = getattr(logging, level_name.upper(), level)

               
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            payload = {
                "level" : record.levelname,
                "message" : record.getMessage(),
                "logger" : record.name,
                "time" : int(time.time() * 1000),
                
            }
            for key in ("request_id","method","path","status","duration_ms","remote_addr"):
                val = getattr(record, key, None)
                if val is not None:
                    payload[key] = val
                    
            if record.exc_info:
                payload["trace"] = "".join(traceback.format_exception(*record.exc_info))
                
            return json.dumps(payload)
    
    handler.setFormatter(JsonFormatter())
    
    app.logger.handlers = [handler]
    app.logger.setLevel(level)
    app.logger.propagate = False

    
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    
    @app.before_request
    def start_time_and_request_id():
        g.start_time = time.time()
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = rid

        
    @app.after_request
    def log_request(response):
        try:
            duration_ms = int((time.time() - g.start_time) * 1000)
        except Exception:
            duration_ms = None
            
        app.logger.info(
            f"{request.method} {request.path} -> {response.status_code}",
            extra={ 
                "request_id" : getattr(g, "request_id", None),
                "method" : request.method,
                "path" : request.path,
                "status" : response.status_code,
                "duration_ms" : duration_ms,
                "remote_addr" : request.headers.get("X-Forwarded-For", request.remote_addr),
                
            }
        )

        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        return response
    
    
    @app.errorhandler(Exception)
    def _handle_unexpected_error(err):
        
        if isinstance(err, HTTPException):
            return err
        
        app.logger.exception(
            "unhandled exception",
            extra={
                "request_id": getattr(g, "request_id", None),
                "path": request.path if request else None,
                "method": request.method if request else None,
            },
        )
        
        return jsonify({"error": "internal_error"}), 500
    
    
    db_url = app.config.get("SQLALCHEMY_DATABASE_URI")

    if not db_url:
        db_url = os.getenv("DATABASE_URL")
        
    if not db_url:
        raise RuntimeError("DATABASE_URL not set in .env")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(bp, url_prefix=f"/api/{app.config.get('API_VERSION', 'v1')}")
    
    return app
