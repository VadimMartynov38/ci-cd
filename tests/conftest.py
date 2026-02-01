import pytest
from datetime import datetime, timedelta
from flask import json
from src.app import create_app, db as _db  # замените yourapp на пакет с вашим create_app

@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    return _db

@pytest.fixture
def sample_data(app, db):
    from src.models import Client, Parking, ClientParking  # путь к моделям
    with app.app_context():
        client = Client(name="Ivan", surname="Petrov", credit_card="1111222233334444", car_number="A111AA")
        db.session.add(client)
        db.session.commit()
        parking = Parking(address="Lenina 1", opened=True, count_places=10, count_available_places=10)
        db.session.add(parking)
        db.session.commit()
        time_in = datetime.utcnow() - timedelta(minutes=5)
        time_out = datetime.utcnow() - timedelta(minutes=1)
        cp = ClientParking(client_id=client.id, parking_id=parking.id, time_in=time_in, time_out=time_out)
        parking.count_available_places -= 1
        db.session.add(cp)
        db.session.add(parking)
        db.session.commit()
        return {"client": client, "parking": parking, "client_parking": cp}
