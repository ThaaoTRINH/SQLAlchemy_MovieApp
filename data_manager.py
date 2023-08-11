# data_manager.py
from random import random
import random
import requests
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from data_models import db, Movie, User, Director, Genre, Star

# db = SQLAlchemy()  # This instance is separate from the one initialized in app.py

def get_the_link_for_person(name):
    """Fetching the details of director or star of movie by going through wikipedia.org"""

    link = f'https://en.wikipedia.org/wiki/{name}'
    return link

def get_movie_details(movie):
    movie_details = {}
    try:
        # fetching movie details from OMDb API
        url = 'https://www.omdbapi.com/?apikey=99b0f16a&t=' + f'{movie.title.lower()}'
        movies_source = requests.get(url)

        # Check if the response status code indicates success (200)
        if movies_source.status_code == 200:
            movies_source = movies_source.json()
            title = movies_source['Title']
            director = movies_source['Director']
            year = movies_source['Released']
            stars = movies_source['Actors']
            genres = movies_source['Genre']
            content = movies_source['Plot']
            awards = movies_source['Awards']
            runtime = movies_source['Runtime']
            poster = movies_source['Poster']

            movie_details = {
                'title': title.upper(),
                'director': director,
                'year': year,
                'stars': stars,
                'genres': genres,
                'content': content,
                'awards': awards,
                'runtime': runtime,
                'poster': poster
            }
        # Process the movies_data as needed
        else:
            print(f"Error: Request returned status code {movies_source.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred while making the request: {e}")
    except ValueError as e:
        print(f"An error occurred while parsing the JSON response: {e}")
    return movie_details


class DataManagerInterface:
    def add_user(self,  first_name, last_name, email, user_name, password):
        pass

    def add_movie(self, title, rating, year_release, director, poster, favorite, user_id):
        pass

    def add_director(self, name, link, movie_id):
        pass

    def add_genre(self, genre, movie_id):
        pass

    def add_star(self, name, link, movie_id):
        pass

    def stars(self):
        pass

    def users(self):
        pass

    def movies(self):
        pass

    def directors(self):
        pass

    def genres(self):
        pass

    def search(self, record_id):
        pass

    def movie_update(self, record_id, new_data):
        pass

    def delete(self, record_id):
        pass

    def find(self, filters):
        pass


# Implement SQLiteDataManager
class SQLiteDataManager(DataManagerInterface):
    def __init__(self):
        self.session = db.session
        self.db = db
        # self.db.init_app(app)

    def movies(self):
        movies = Movie.query.all()
        return movies

    def users(self):
        users = User.query.all()
        return users

    def directors(self):
        directors = Director.query.all()
        return directors

    def genres(self):
        genres = Genre.query.all()
        return genres

    def stars(self):
        stars = Star.query.all()
        return stars

    def add_user(self, first_name, last_name, email, user_name, password):
        new_user = User(first_name, last_name, email, user_name, password)
        self.db.session.add(new_user)
        self.db.session.commit()

    def add_movie(self, title, rating, year_release, director, poster, favorite, user_id):
        new_movie = Movie(title=title, rating=rating, year_release=year_release,
                          director=director, poster=poster, favorite=favorite,
                          user_id=user_id)
        self.db.session.add(new_movie)
        self.db.session.commit()

    def add_genre(self, genre, movie_id):
        new_genre = Genre(genre=genre, movie_id=movie_id)
        self.db.session.add(new_genre)
        self.db.session.commit()

    def add_director(self, name, link, movie_id):
        try:
            new_director = Director(name=name, link=link, movie_id=movie_id)
            self.db.session.add(new_director)
            self.db.session.commit()
        except Exception:
            self.db.session.rollback()  #

    def add_star(self, name, link, movie_id):
        try:
            new_star = Star(name=name, link=link, movie_id=movie_id)
            self.db.session.add(new_star)
            self.db.session.commit()
        except Exception:
            self.db.session.rollback()  #

    def movie_by_title(self, title):
        try:
            movies = self.session.query(Movie).filter(Movie.title.ilike(f"%{title}%")).all()
            return movies
        except Exception:
            print(f"An error occurred:")
            return None

    def movie_by_rating(self, rating):
        try:
            formatted_rating = float(rating)
            tolerance = 0.1
            lower_bound = formatted_rating - tolerance
            upper_bound = formatted_rating + tolerance
            movies = self.session.query(Movie).filter(and_(Movie.rating >= lower_bound,
                                                           Movie.rating <= upper_bound)).all()
            return movies
        except ValueError:
            print(f"Error converting rating to float")
            return None
        except SQLAlchemyError:
            print(f"An error occurred")
            return None

    def movies_by_user(self, first_name):
        try:
            movies = self.session.query(Movie).join(User).filter(User.first_name.ilike(f"%{first_name}%")).all()
            return movies
        except Exception:
            print(f"An error occurred")
            return None

    def movies_by_director(self, director_name):
        try:
            movies = self.session.query(Movie).filter(Movie.director.ilike(f"%{director_name}%")).all()
            return movies
        except Exception:
            print(f"An error occurred")
            return None

    def movies_by_star(self, star_name):
        try:
            movies = self.session.query(Movie).join(Movie.stars).filter(Star.name.ilike(f"%{star_name}%")).all()
            return movies
        except Exception:
            print(f"An error occurred")
            return None

    def movies_by_genre(self, genre):
        try:
            movies = self.session.query(Movie).join(Movie.genres).filter(Genre.genre.ilike(f"%{genre}%")).all()
            return movies
        except Exception:
            print(f"An error occurred")
            return None

    def movie_update(self, record_id, new_data):
        movie_update = self.session.query(Movie).filter(Movie.id == record_id).first()

        if movie_update:
            # update the attributes using the new_data dictionary
            for key, value in new_data.items():
                """ setattr is a function in Python to used to set the value of an attribute 
                on an object dynamically"""
                setattr(movie_update, key, value)

            # commit the changes to the database
            self.session.commit()
            return True
        else:
            return False

    def update_user(self, user_id, data):
        """
        Update an existing user's information in the database.
        Args:
            user_id (int): ID of the user to update.
            data (dict): Updated user information.
        Returns:
            bool: True if the user was updated successfully, False otherwise.
        """
        try:
            user = self.db.session.query(User).filter_by(id=user_id).first()
            if user:
                user.first_name = data.get('first_name', user.first_name)
                user.last_name = data.get('last_name', user.last_name)
                user.email = data.get('email', user.email)
                user.user_name = data.get('user_name', user.user_name)
                user.password = data.get('password', user.password)

                self.db.session.commit()
                return True
            else:
                return False
        except Exception:
            self.db.session.rollback()
            return False

    def delete_user(self, user_id):
        """
        Delete an existing user from the database.
        Args:
            user_id (int): ID of the user to delete.
        Returns:
            bool: True if the user was deleted successfully, False otherwise.
        """
        try:
            user = self.db.session.query(User).filter_by(id=user_id).first()
            if user:
                self.db.session.delete(user)
                self.db.session.commit()
                return True
            else:
                return False
        except Exception:
            self.db.session.rollback()
            return False

    def get_user_data(self, user_id):
        user = self.session.query(User).filter(User.id == user_id).first()
        return user

    def top_rating_movies(self):
        """
        One of the top of recommendation for movies,
        the function allows the users to fetch 10 movies with top rating.
        :return: 12 top rating films
        """
        top_movies = self.session.query(Movie).order_by(Movie.rating.desc()).limit(12).all()
        return top_movies

    def recommendation_movie(self):
        """
        Recommendation movie rom existing database,
        based on movie_id randomly picked
        :return: 1 film
        """
        # Query all movies and extract their IDs
        movie_ids = [movie.id for movie in db.session.query(Movie).all()]
        recommendation_movie_id = random.choice(movie_ids)
        movie = self.db.session.query(Movie).filter_by(id=recommendation_movie_id).first()
        return movie
