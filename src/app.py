from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from sqlalchemy.sql import text, select
import sys

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)


class Tari(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nume_tara = db.Column(db.String(80), unique=True)
    latitudine = db.Column(db.Float)
    longitudine = db.Column(db.Float)

    def __init__(self, nume_tara, latitudine, longitudine, id=None):
        self.id = id
        self.nume_tara = nume_tara
        self.latitudine = latitudine
        self.longitudine = longitudine


class Orase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_tara = db.Column(db.Integer)
    nume_oras = db.Column(db.String(80))
    latitudine = db.Column(db.Float)
    longitudine = db.Column(db.Float)

    __table_args__ = (
        db.UniqueConstraint('id_tara', 'nume_oras'),
    )

    def __init__(self, id, id_tara, nume_oras, latitudine, longitudine):
        self.id = id
        self.id_tara = id_tara
        self.nume_oras = nume_oras
        self.latitudine = latitudine
        self.longitudine = longitudine


class Temperaturi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valoare = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, server_default=text("NOW()"), default=datetime.datetime.utcnow())
    id_oras = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint('id_oras', 'timestamp'),
    )

    def __init__(self, id, valoare, id_oras):
        self.id = id
        self.valoare = valoare
        self.timestamp = timestamp
        self.id_oras = id_oras


db.create_all()

@app.route('/api/countries', methods=['POST'])
def add_country():
    body = request.get_json()

    # check if we have all required columns
    if {"nume", "lat", "lon"} != body.keys():
        return Response(status=400)

    # check if there already exists a country with that name
    if Tari.query.filter(Tari.nume_tara == body['nume']).first():
        return Response(status=409)

    db.session.add(Tari(nume_tara=body['nume'], longitudine=body['lon'], latitudine=body['lat']))
    db.session.commit()

    #print(Tari.query.filter_by(nume_tara=body['nume']).first().id, file=sys.stderr)

    test_data = {'id': Tari.query.filter_by(nume_tara=body['nume']).first().id}
    return jsonify(test_data), 201

# taken from https://stackoverflow.com/questions/1958219/how-to-convert-sqlalchemy-row-object-to-a-python-dict
# Anurag Uniyal's answer
row2dict = lambda col_names, r: {column_name: getattr(r, c.name) for (column_name, c) in zip(col_names, r.__table__.columns)}

@app.route('/api/countries', methods=['GET'])
def list_countries():
    all_countries = Tari.query.all()

    # reformat them in the desired format
    columns_names = ['id', 'nume', 'lat', 'lon']
    all_countries_reformated = [row2dict(columns_names, country) for country in all_countries]

    print(all_countries_reformated, file=sys.stderr)

    return jsonify(all_countries_reformated), 200

# @app.route('/items/<id>', methods=['GET'])
# def get_item(id):
#     item = Item.query.get(id)
#     del item.__dict__['_sa_instance_state']
#     return jsonify(item.__dict__)

# @app.route('/items', methods=['GET'])
# def get_items():
#     items = []
#     for item in db.session.query(Item).all():
#         del item.__dict__['_sa_instance_state']
#         items.append(item.__dict__)
#     return jsonify(items)

# @app.route('/items', methods=['POST'])
# def create_item():
#     body = request.get_json()
#     db.session.add(Item(body['title'], body['content']))
#     db.session.commit()
#     return "item created"

# @app.route('/items/<id>', methods=['PUT'])
# def update_item(id):
#     body = request.get_json()
#     db.session.query(Item).filter(Item.id == id).update({Item.title: body['title'], Item.content: body['content']})
#     db.session.commit()
#     return "item updated"

# @app.route('/items/<id>', methods=['DELETE'])
# def delete_item(id):
#     db.session.query(Item).filter(Item.id == id).delete()
#     db.session.commit()
#     return "item deleted"