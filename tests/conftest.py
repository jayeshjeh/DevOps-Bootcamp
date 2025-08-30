
import pytest
from app import create_app
from extensions import db
from app.config import TestConfig

@pytest.fixture
def client():
    
    app = create_app(TestConfig)    
    
    # app = create_app({
    #     "TESTING" : True,
    #     "SQLALCHEMY_DATABASE_URI" : "sqlite:///:memory:",
    #     "SQLLCHEMY_TRACK_MODIFICATIONS" : False,
    #     "API_VERSION" : "v2"
    # })
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        
    with app.test_client() as c:
        api_version = app.config.get("API_VERSION", "v1")
        c.api_base = f"/api/{api_version}"
        yield c
        
        