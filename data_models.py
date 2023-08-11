import os
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask import Flask

# get the root directory
ROOT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
file_path = os.path.join(ROOT_DIRECTORY, 'data', 'hollywood.sqlite')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{file_path}'
db = SQLAlchemy(app)

Base = db.Model

# Defile the User model
class User(Base, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    username = db.Column(db.String)
    password = db.Column(db.String)
    is_active = db.Column(db.Boolean, default=True)

    def get_id(self):
        return self.id

    def __init__(self, first_name, last_name, email, username, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User id={self.id}, username = {self.username}>'

    def __str__(self):
        return f'The first name of user is {self.first_name.upper()}, ' \
               f'and last name is {self.last_name.upper()}'

# Define the Movie model
class Movie(Base):
    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, unique=True)
    rating = db.Column(db.Float)
    year_release = db.Column(db.Integer)
    director = db.Column(db.String)
    poster = db.Column(db.String)
    favorite = db.Column(db.Integer)

    # create a foreign key relationship to table users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # define a relationship with the User model
    user = relationship('User', backref=db.backref('movies'))

    def __repr__(self):
        return f"<Movie id={self.id}, title='{self.title}'>"

    def __str__(self):
        return f'{self.title}, with rating is {self.rating}'

class Director(Base):
    __tablename__ = 'directors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    link = db.Column(db.String)

    def __init__(self, name, link, movie_id):
        self.name = name
        self.link = link
        self.movie_id = movie_id

    # create a foreign key relationship to table movies
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))

    # define a relationship with the Movie model
    movie = relationship('Movie', backref=db.backref('directors'))

    def __repr__(self):
        return f"<Director id={self.id}, name='{self.name}'>"

    def __str__(self):
        return f'Director: {self.name},details is {self.link}'

class Genre(Base):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    genre = db.Column(db.String)

    def __init__(self, genre, movie_id):
        self.genre = genre
        self.movie_id = movie_id

    # create a foreign key relationship to table movies
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))

    # define a relationship with the Movie model
    movie = relationship('Movie', backref=db.backref('genres'))

    def __repr__(self):
        return f"<Genre id={self.id}, name='{self.genre}'>"

    def __str__(self):
        return f'Genre id: {self.id}, name={self.genre}'

class Star(Base):
    __tablename__ = 'stars'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    link = db.Column(db.String)

    def __init__(self, name, link, movie_id):
        self.name = name
        self.link = link
        self.movie_id = movie_id

    # create a foreign key relationship to table movies
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))

    # define a relationship with the User model
    movie = relationship('Movie', backref=db.backref('stars'))

    def __repr__(self):
        return f"<Star id={self.id}, name='{self.name}'>"

    def __str__(self):
        return f'Star: {self.name}, details is {self.link}'
