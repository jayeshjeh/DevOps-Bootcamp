import os

class BaseConfig:
    APP_NAME = "student_api"
    ENV_NAME = "development"
    API_VERSION = "v2"
    APP_OWNER = os.getenv("APP_OWNER", "unknown")
    BUILD_NUM = os.getenv("BUILD_NUM", "dev")
    
class DevConfig(BaseConfig):
    ENV_NAME = "development"
    DEBUG=True
    
class TestConfig(BaseConfig):
    ENV_NAME = "testing"
    TESTING = True
    DEBUG= True
    SQLALCHEMY_DATABASE_URI = "sqlite:///memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_VERSION = "v2"
    
class ProdConfig(BaseConfig):
    ENV_NAME = "production"
    DEBUG=False
    
    
def get_config():
    env = os.getenv("FLASK_ENV", "development")
    
    return {
        "development" : DevConfig,
        "testing" : TestConfig,
        "production" : ProdConfig
    }.get(env, DevConfig)
    
    