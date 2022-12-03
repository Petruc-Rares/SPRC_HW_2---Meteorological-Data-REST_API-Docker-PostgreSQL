from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from sqlalchemy.sql import text, select
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
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

    def __init__(self, id_tara, nume_oras, latitudine, longitudine, id=None):
        self.id = id
        self.id_tara = id_tara
        self.nume_oras = nume_oras
        self.latitudine = latitudine
        self.longitudine = longitudine


class Temperaturi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valoare = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, server_default=text("NOW()"))

    id_oras = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint('id_oras', 'timestamp'),
    )

    def __init__(self, valoare, id_oras, id=None, timestamp=None):
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


        # check if data types are correct
    if not ((isinstance(body['lon'], float)) and
            (isinstance(body['nume'], str)) and
            (isinstance(body['lat'], float))):
        return Response(status=400)

    # add the new country
    # check uk, pk
    try:
        db.session.add(Tari(nume_tara=body['nume'], longitudine=body['lon'], latitudine=body['lat']))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return Response(status=409)

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

    return jsonify(all_countries_reformated), 200

@app.route("/api/countries/<int:id_country>", methods=["PUT"])
def modify_country(id_country):
    body = request.get_json()

    # check if we have all required columns
    if {"id", "nume", "lat", "lon"} != body.keys():
        return Response(status=400)

    # check if the country id does not exist
    # in this case return error
    if not Tari.query.filter(Tari.id == id_country).first():
        return Response(status=404)

    # check if data types are correct
    if not ((isinstance(body['id'], int)) and
            (isinstance(body['lon'], float)) and
            (isinstance(body['nume'], str)) and
            (isinstance(body['lat'], float))):
        return Response(status=400) 

    try:
        db.session.query(Tari).\
                    filter(Tari.id == id_country).\
                    update({'id':body['id'],
                            'nume_tara':body['nume'],
                            'longitudine': body['lon'],
                            'latitudine': body['lat']})
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return Response(status=400)

    return Response(status=200)


@app.route("/api/countries/<int:id_country>", methods=["DELETE"])
def delete_country(id_country):
    # check if the country id does not exist
    # in this case return error
    if not Tari.query.filter(Tari.id == id_country).first():
        return Response(status=404)

    db.session.query(Tari).\
                filter(Tari.id == id_country).\
                delete()

    db.session.commit()

    return Response(status=200)

@app.route('/api/cities', methods=['POST'])
def add_city():
    body = request.get_json()

    # check if we have all required columns
    if {"idTara", "nume", "lat", "lon"} != body.keys():
        return Response(status=400)

    # check if data types are correct
    if not ((isinstance(body['lat'], float)) and
            (isinstance(body['lon'], float)) and
            (isinstance(body['nume'], str)) and
            (isinstance(body['idTara'], int))):
        return Response(status=400)

    # add the new city
    # check uk, pk
    try:
        db.session.add(Orase(id_tara = body['idTara'],nume_oras=body['nume'], longitudine=body['lon'], latitudine=body['lat']))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return Response(status=400)

    test_data = {'id': db.session.query(Orase).filter(and_(Orase.nume_oras==body['nume'], Orase.id_tara == body['idTara'])).first().id}
    return jsonify(test_data), 201

@app.route('/api/cities', methods=['GET'])
def list_cities():
    all_cities = Orase.query.all()

    # reformat them in the desired format
    columns_names = ['id', 'idTara', 'nume', 'lat', 'lon']
    all_cities_reformated = [row2dict(columns_names, city) for city in all_cities]

    return jsonify(all_cities_reformated), 200

@app.route('/api/cities/country/<int:id_country>', methods=['GET'])
def get_city_of_country(id_country):
    all_cities = db.session.query(Orase).filter(Orase.id_tara==id_country).all()

    # reformat them in the desired format
    columns_names = ['id', 'idTara', 'nume', 'lat', 'lon']
    all_cities_reformated = [row2dict(columns_names, city) for city in all_cities]

    return jsonify(all_cities_reformated), 200

@app.route('/api/cities/<int:id_city>', methods=['PUT'])
def modify_city(id_city):
    body = request.get_json()

    # check if we have all required columns
    if {"id", "idTara", "nume", "lat", "lon"} != body.keys():
        return Response(status=400)

    # check if data types are correct
    if not ((isinstance(body['lat'], float)) and
            (isinstance(body['lon'], float)) and
            (isinstance(body['nume'], str)) and
            (isinstance(body['idTara'], int)) and
            (isinstance(body['id'], int))):
        return Response(status=400)    

    if not Orase.query.filter(Orase.id == id_city).first():
        return Response(status=404)


    # try to modify existing id
    # check no pk or uk violation
    try:
        db.session.query(Orase).\
            filter(Orase.id == id_city).\
            update({'id':body['id'],
                    'id_tara': body['idTara'],
                    'nume_oras':body['nume'],
                    'longitudine': body['lon'],
                    'latitudine': body['lat']})
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return Response(status=400)

    return Response(status=200)

@app.route("/api/cities/<int:id_city>", methods=["DELETE"])
def delete_city(id_city):
    city_to_delete = Orase.query.filter(Orase.id == id_city).first()

    # check non-existent city to delete
    if not city_to_delete:
        return Response(status=404)

    # do the delete
    db.session.query(Orase).\
                filter(Orase.id == id_city).\
                delete()
    db.session.commit()

    return Response(status=200)

@app.route('/api/temperatures', methods=['POST'])
def add_temperature():
    body = request.get_json()

    # check if we have all required columns
    if {"idOras", "valoare"} != body.keys():
        return Response(status=400)


        # check if data types are correct
    if not ((isinstance(body['idOras'], int)) and
            (isinstance(body['valoare'], float))):
        return Response(status=400)


    # add the new country
    # check uk, pk
    try:
        timestamp_generated = datetime.datetime.utcnow()
        db.session.add(Temperaturi(id_oras=body['idOras'], valoare=body['valoare'], timestamp=timestamp_generated))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return Response(status=409)

    test_data = {'id': Temperaturi.query.filter(and_(Temperaturi.id_oras==body['idOras'], Temperaturi.timestamp==timestamp_generated)).first().id}
    return jsonify(test_data), 201

@app.route('/api/temperatures', methods=['GET'])
def search():
    args = request.args
    lat = args.get('lat')
    lon = args.get('lon')
    from_date = args.get('from')
    until_date = args.get('until')

    info = db.session.query(Temperaturi)

    if lat is not None and lon is not None:
        lat = float(lat)
        lon = float(lon)

        info = info.filter(Orase.id==Temperaturi.id_oras).\
             filter(Orase.latitudine==lat).\
             filter(Orase.longitudine==lon)
    elif lat is not None:
        lat = float(lat)

        info = info.filter(Orase.id==Temperaturi.id_oras).\
             filter(Orase.latitudine==lat)
    elif lon is not None:
        lon = float(lon)

        info = info.filter(Orase.id==Temperaturi.id_oras).\
             filter(Orase.longitudine==lon)
    
    if from_date is not None:
        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        info = info.filter(Temperaturi.timestamp >= from_date)
    
    if until_date is not None:
        until_date = datetime.datetime.strptime(until_date, '%Y-%m-%d')
        info = info.filter(Temperaturi.timestamp <= until_date)

    # reformat them in the desired format
    columns_names = ['id', 'valoare', 'timestamp']
    info_reformatted = [row2dict(columns_names, result) for result in info]

    return jsonify(info_reformatted), 200

@app.route('/api/temperatures/cities/<int:id_city>', methods=['GET'])
def search_2(id_city):
    args = request.args
    from_date = args.get('from')
    until_date = args.get('until')

    info = db.session.query(Temperaturi).filter(Temperaturi.id_oras==id_city)

    if from_date is not None:
        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        info = info.filter(Temperaturi.timestamp >= from_date)
    
    if until_date is not None:
        until_date = datetime.datetime.strptime(until_date, '%Y-%m-%d')
        info = info.filter(Temperaturi.timestamp <= until_date)

    # reformat them in the desired format
    columns_names = ['id', 'valoare', 'timestamp']
    info_reformatted = [row2dict(columns_names, result) for result in info]

    return jsonify(info_reformatted), 200

@app.route('/api/temperatures/countries/<int:id_country>', methods=['GET'])
def search_3(id_country):
    args = request.args
    from_date = args.get('from')
    until_date = args.get('until')

    info = db.session.query(Temperaturi).filter(Tari.id==id_country).\
                                  filter(Tari.id == Orase.id_tara).\
                                  filter(Orase.id == Temperaturi.id_oras)

    if from_date is not None:
        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        info = info.filter(Temperaturi.timestamp >= from_date)
    
    if until_date is not None:
        until_date = datetime.datetime.strptime(until_date, '%Y-%m-%d')
        info = info.filter(Temperaturi.timestamp <= until_date)

    # reformat them in the desired format
    columns_names = ['id', 'valoare', 'timestamp']
    info_reformatted = [row2dict(columns_names, result) for result in info]

    return jsonify(info_reformatted), 200

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