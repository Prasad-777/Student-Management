from app import app

def test_home_page():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/")
