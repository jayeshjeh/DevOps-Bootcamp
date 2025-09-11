from logging import INFO
import logging
import os

class BaseConfig:
    APP_NAME = "student_api"
    ENV_NAME = "development"
    API_VERSION = "v2"
    APP_OWNER = os.getenv("APP_OWNER", "Jayesh")
    BUILD_NUM = os.getenv("BUILD_NUM", "dev")
    LOG_LEVEL = INFO
    
class DevConfig(BaseConfig):
    ENV_NAME = "development"
    DEBUG=True
    LOG_LEVEL = logging.DEBUG
    
class TestConfig(BaseConfig):
    ENV_NAME = "testing"
    TESTING = True
    DEBUG= True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_VERSION = "v2"
    LOG_LEVEL = logging.DEBUG
    
class ProdConfig(BaseConfig):
    ENV_NAME = "production"
    DEBUG=False
    LOG_LEVEL= logging.INFO

    
def get_config():
    env = os.getenv("FLASK_ENV", "development")
    
    return {
        "development" : DevConfig,
        "testing" : TestConfig,
        "production" : ProdConfig
    }.get(env, DevConfig)
    
    