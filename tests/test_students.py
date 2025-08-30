import pytest

def create_student(client, **overrides):
    payload = {
        "name" : "User1",
        "age" : 20,
        "grade" : "A",
        "email" : "user1@work.com"
    }
    payload.update(overrides)
    r = client.post(f"{client.api_base}/students", json=payload)
    assert r.status_code in (200, 201)
    return r.get_json()


def test_get_student_200(client):
    s = create_student(client)
    r = client.get(f"{client.api_base}/students/{s['id']}")
    assert r.status_code == 200
    body = r.get_json()
    assert body["id"] == s["id"]
    assert body["email"] == "user1@work.com"

def test_get_student_404(client):
    r = client.get(f"{client.api_base}/students/99999")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"
    
    
def test_delete_student_204(client):
    s = create_student(client)
    r = client.delete(f"{client.api_base}/students/{s['id']}")
    assert r.status_code == 204
    
    r = client.delete(f"{client.api_base}/students/{s['id']}")
    assert r.status_code == 404



def test_put_update_student_200_partial_allowed(client):
    s = create_student(client)
    r = client.put(
        f"{client.api_base}/students/{s['id']}",
        json={"name" : "User1 update"}
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["name"] == "User1 update"
    assert body["email"] == "user1@work.com"
    
def test_put_update_404(client):
    
    r = client.put(f"{client.api_base}/students/99999", json={"name" : "User07"})
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"


def test_put_int_400(client):
    s = create_student(client)
    r = client.put(f"{client.api_base}/students/{s['id']}", json={"age" : "twenty"})
    assert r.status_code == 400
    
def test_update_email_duplicate_returns_409(client):
    
    r = client.post(f"{client.api_base}/students", json={
        "name": "A",
        "age": 18,
        "grade": "A",
        "email": "a@example.com",
    })
    assert r.status_code == 201
    a = r.get_json()

    
    r = client.post(f"{client.api_base}/students", json={
        "name": "B",
        "age": 19,
        "grade": "B",
        "email": "b@example.com",
    })
    assert r.status_code == 201
    b = r.get_json()


    r = client.put(f"{client.api_base}/students/{b["id"]}", json={
        "email": "a@example.com"
    })
    assert r.status_code == 409
    data = r.get_json()
    assert data["error"] == "conflict"
    assert "email" in data["detail"].lower()

        
        