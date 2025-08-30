        
        
def test_health(client):
    response = client.get(f"{client.api_base}/health")
    
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["service"] == "student_api"

