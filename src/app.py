"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from sqlalchemy import select
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Profile, Car, Favourite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# GET ALL USERS ----->
@app.route('/users', methods=['GET'])   
def get_users():
    stmt = select(User)
    users = db.session.execute(stmt).scalars().all()
    return jsonify([user.serialize() for user in users]), 200


# GET SINGLE USER ----->
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({'error':'User not found'}), 404
    return jsonify(user.serialize()),200


# POST USER ------->
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data or 'age' not in data:
        return jsonify({'error':'Missing data'}), 400

    # Crear usuario
    new_user = User(
        email=data['email'],
        password=data['password'],
        age=data['age']
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.serialize()), 200

# DELETE USER 
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({'error':'User not found'}), 404
    if user.profile:
        db.session.delete(user.profile)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message':'user deleted'}),200

# PUT USER
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({'error':'User not found'}), 404
    user.email = data.get('email',user.email)
    user.age = data.get('age',user.age)
    user.password = data.get('password',user.password)
    db.session.commit()
    return jsonify(user.serialize()),200


# GET ALL PROFILES
@app.route('/users/profile', methods=['GET'])   
def get_users_profile():
    stmt = select(Profile)
    users = db.session.execute(stmt).scalars().all()
    return jsonify([user.serialize() for user in users]), 200



# GET SINGLE USER PROFILE ----->
@app.route('/users/<int:user_id>/profile', methods=['GET'])
def get_single_user_profile(user_id):
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({'error':'User not found'}), 404
    return jsonify(user.profile.serialize()),200


# PUT SINGLE USER PROFILE ------>
@app.route('/users/<int:user_id>/profile', methods=['PUT'])
def update_user_profile(user_id):
    data = request.get_json()
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    
    if user is None:
        return jsonify({'error':'User not found'}), 404
    if user.profile is None:
        return jsonify({'error':'This user has not profile create it using a "POST"'})
    
    user.profile.title = data.get('title',user.profile.title)
    user.profile.bio = data.get('bio',user.profile.bio)
    db.session.commit()
    return jsonify(user.profile.serialize()),200


# DELETE USER PROFILE ------>
@app.route('/users/<int:user_id>/profile', methods=['DELETE'])
def delete_user_profile(user_id):
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()

    if user is None:
        return jsonify({'error': 'User not found'}), 404

    if user.profile is None:
        return jsonify({'error': 'This user do not have a profile'}), 404

    db.session.delete(user.profile)
    db.session.commit()

    return jsonify({'message': 'User profile deleted'}), 200

# POST SINGLE USE PROFILE ------> 
@app.route('/users/<int:user_id>/profile', methods=['POST'])
def create_user_profile(user_id):
    data = request.get_json()

    if not data or 'title' not in data or 'bio' not in data:
        return jsonify({'error':'Missing data'}), 400
    
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    if user.profile:
        return jsonify({'error': 'User already have a profile, select "PUT" insted of "POST" '}), 404
    else:
        new_profile = Profile(title=data['title'], bio=data['bio'])
        user.profile = new_profile
    db.session.commit()
    return jsonify(user.profile.serialize()), 200


# GET ALL CARS
@app.route('/cars', methods=['GET'])   
def get_cars():
    stmt = select(Car)
    cars = db.session.execute(stmt).scalars().all()
    return jsonify([car.serialize() for car in cars]), 200



#GET SINGLE CAR
@app.route('/cars/<int:car_id>', methods=['GET'])
def get_single_car(car_id):
    stmt = select(Car).where(Car.id == car_id)
    car = db.session.execute(stmt).scalar_one_or_none()
    if car is None:
        return jsonify({'error':'car not found'}), 404
    return jsonify(car.serialize()),200



# POST CAR
@app.route('/cars', methods=['POST'])
def create_car():
    data = request.get_json()
    required_fields = ['model', 'year', 'name']

    if not data or any(field not in data for field in required_fields):
        return jsonify({'error': 'Missing data'}), 400

    user_id = data.get('user_id')  # Puede venir o no

    # Si viene user_id, validarlo
    if user_id:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

    new_car = Car(
        name=data['name'],
        year=data['year'],
        model=data['model'],
        user_id=user_id  # Esto puede ser None
    )

    db.session.add(new_car)
    db.session.commit()

    return jsonify(new_car.serialize()), 201


#DELETE CAR
@app.route('/cars/<int:car_id>', methods=['DELETE'])
def delete_car(car_id):
    stmt = select(Car).where(Car.id == car_id)
    car = db.session.execute(stmt).scalar_one_or_none()
    if car is None:
        return jsonify({'error':'car not found'}), 404
    db.session.delete(car)
    db.session.commit()
    return jsonify({'message':'user deleted'}),200



# PUT SINGLE CAR ------>
@app.route('/cars/<int:car_id>', methods=['PUT'])
def update_car(car_id):
    data = request.get_json()
    stmt = select(Car).where(Car.id == car_id)
    car = db.session.execute(stmt).scalar_one_or_none()
    
    if car is None:
        return jsonify({'error':'User not found'}), 404    

    car.model = data.get('model',car.model)
    car.year = data.get('year',car.year)
    car.name = data.get('name',car.name)
    db.session.commit()
    return jsonify(car.serialize()),200


#GET ALL FAVOURITES
@app.route('/favourites', methods=['GET'])   
def get_favourites():
    stmt = select(Favourite)
    favourites = db.session.execute(stmt).scalars().all()
    return jsonify([favourite.serialize() for favourite in favourites]), 200


#GET SINGLE FAVOURITE
@app.route('/favourites/<int:favourite_id>', methods=['GET'])
def get_single_favourite(favourite_id):
    stmt = select(Favourite).where(Favourite.id == favourite_id)
    favourite = db.session.execute(stmt).scalar_one_or_none()
    if favourite is None:
        return jsonify({'error':'Favourite not found'}), 404
    return jsonify(favourite.serialize()),200

#POST FAVOURITES
@app.route('/favourites/<int:user_id>/<int:car_id>', methods=['POST'])
def add_favourite(user_id, car_id):
    user = db.session.get(User, user_id)
    car = db.session.get(Car, car_id)

    if not user or not car:
        return jsonify({'error': 'User or Car not found'}), 404

    # Comprobar si ya está marcado como favorito
    existing = db.session.execute(
        select(Favourite).where(Favourite.user_id == user_id, Favourite.car_id == car_id)
    ).scalar_one_or_none()

    if existing:
        return jsonify({'error': 'This car is already in favourites'}), 400

    favourite = Favourite(user_id=user_id, car_id=car_id)
    db.session.add(favourite)
    db.session.commit()

#PUT FAVOURITES
@app.route('/favourites/<int:fav_id>', methods=['PUT'])
def update_favourite(fav_id):
    data = request.get_json()
    favourite = db.session.get(Favourite, fav_id)

    if favourite is None:
        return jsonify({'error': 'Favourite not found'}), 404

    new_user_id = data.get('user_id')
    new_car_id = data.get('car_id')

    if new_user_id:
        favourite.user_id = new_user_id
    if new_car_id:
        favourite.car_id = new_car_id

    db.session.commit()
    return jsonify(favourite.serialize()), 200




# DELETE FAVOURITE
@app.route('/favourites/<int:favourite_id>', methods=['DELETE'])
def delete_favourite(favourite_id):
    stmt = select(Favourite).where(Favourite.id == favourite_id)
    favourite = db.session.execute(stmt).scalar_one_or_none()
    if favourite is None:
        return jsonify({'error':'favourite not found'}), 404
    db.session.delete(favourite)
    db.session.commit()
    return jsonify({'message':'favourite deleted'}),200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

