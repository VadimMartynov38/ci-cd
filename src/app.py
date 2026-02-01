from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db: SQLAlchemy = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parkings.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    from .models import Client, ClientParking, Parking

    with app.app_context():
        db.create_all()
        app.models = {
            "Client": Client,
            "Parking": Parking,
            "ClientParking": ClientParking,
        }

    @app.route("/clients", methods=["GET"])
    def list_clients():
        clients = Client.query.all()
        return jsonify([c.to_dict() for c in clients]), 200

    @app.route("/clients/<int:client_id>", methods=["GET"])
    def get_client(client_id):
        c = Client.query.get(client_id)
        if not c:
            return jsonify({"error": "client not found"}), 404
        return jsonify(c.to_dict()), 200

    @app.route("/clients", methods=["POST"])
    def create_client():
        data = request.get_json(force=True)
        name = data.get("name")
        surname = data.get("surname")
        if not name or not surname:
            return jsonify({"error": "name and surname required"}), 400
        client = Client(
            name=name,
            surname=surname,
            credit_card=data.get("credit_card"),
            car_number=data.get("car_number"),
        )
        db.session.add(client)
        db.session.commit()
        return jsonify(client.to_dict()), 201

    @app.route("/parkings", methods=["POST"])
    def create_parking():
        data = request.get_json(force=True)
        address = data.get("address")
        count_places = data.get("count_places")
        if not address or count_places is None:
            return jsonify({"error": "address and count_places required"}), 400
        try:
            cp = int(count_places)
        except (TypeError, ValueError):
            return jsonify({"error": "count_places must be integer"}), 400
        parking = Parking(
            address=address, opened=True, count_places=cp, count_available_places=cp
        )
        db.session.add(parking)
        db.session.commit()
        return jsonify(parking.to_dict()), 201

    @app.route("/client_parkings", methods=["POST"])
    def enter_parking():
        data = request.get_json(force=True)
        client_id = data.get("client_id")
        parking_id = data.get("parking_id")
        if client_id is None or parking_id is None:
            return jsonify({"error": "client_id and parking_id required"}), 400
        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": "client not found"}), 404
        parking = Parking.query.get(parking_id)
        if not parking:
            return jsonify({"error": "parking not found"}), 404
        if not parking.opened:
            return jsonify({"error": "parking is closed"}), 400
        if parking.count_available_places <= 0:
            return jsonify({"error": "no available places"}), 400
        existing = ClientParking.query.filter_by(
            client_id=client_id, parking_id=parking_id, time_out=None
        ).first()
        if existing:
            return (
                jsonify(
                    {
                        "error": "active parking session already exists "
                        "for this client on this parking"
                    }
                ),
                400,
            )
        cp = ClientParking(
            client_id=client_id, parking_id=parking_id, time_in=datetime.utcnow()
        )
        try:
            parking.count_available_places -= 1
            db.session.add(cp)
            db.session.add(parking)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"error": "internal error"}), 500
        return jsonify(cp.to_dict()), 201

    @app.route("/client_parkings", methods=["DELETE"])
    def exit_parking():
        data = request.get_json(force=True)
        client_id = data.get("client_id")
        parking_id = data.get("parking_id")
        if client_id is None or parking_id is None:
            return jsonify({"error": "client_id and parking_id required"}), 400
        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": "client not found"}), 404
        parking = Parking.query.get(parking_id)
        if not parking:
            return jsonify({"error": "parking not found"}), 404
        cp = ClientParking.query.filter_by(
            client_id=client_id, parking_id=parking_id, time_out=None
        ).first()
        if not cp:
            return jsonify({"error": "active parking session not found"}), 404
        if not client.credit_card:
            return jsonify({"error": "no credit card attached; cannot charge"}), 400
        cp.time_out = datetime.utcnow()
        duration_seconds = (cp.time_out - cp.time_in).total_seconds()
        hours = int((duration_seconds + 3599) // 3600)
        amount = hours * 1.0
        payment_ok = True
        if not payment_ok:
            return jsonify({"error": "payment failed"}), 402
        try:
            parking.count_available_places += 1
            db.session.add(cp)
            db.session.add(parking)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"error": "internal error"}), 500
        return (
            jsonify(
                {"client_parking": cp.to_dict(), "charged": amount, "currency": "USD"}
            ),
            200,
        )

    return app
