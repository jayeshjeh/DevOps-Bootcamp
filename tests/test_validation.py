
def test_missing_fields_returns_400(client):
    
    payload ={
        "name" : "User2",
        "age" : 18,
        "grade" : "B+"
    }
    
    response = client.post(f"{client.api_base}/students", json=payload)
    
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert "Missing fields" in data["detail"]
    assert "email" in data["detail"]
    
    
    
def test_age_int_400(client):
    payload = {
        "name" : "User4",
        "age" : "twenty",
        "grade" : "A",
        "email" : "user4@example.com"
    }
    
    
    response = client.post(f"{client.api_base}/students", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert "age" in data["detail"].lower()
    
    