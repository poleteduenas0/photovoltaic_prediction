# from src.your_project_code.example import add


# def test_add():
#     assert add(2, 3) == 5

def test_example():
    # Simulate the service response
    response = {
        "user_role": "user",
        "status_code": 200
    }
    assert response["user_role"] == "user"
    assert response["status_code"] == 200