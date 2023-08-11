# app.py
import os
import re
from random import random
from sqlite3 import IntegrityError

import requests as requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template, redirect, flash, jsonify, Blueprint, session, url_for
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_mail import Message, Mail

import data_manager
from data_manager import SQLiteDataManager
from data_models import db, Movie, User

# create a flask instance
app = Flask(__name__)

api = Blueprint('api', __name__)

# import and configure with mail server setting
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thao.mym@gmail.com'
app.config['MAIL_PASSWORD'] = 'Thao@1978'
mail = Mail(app)

# get the root directory
ROOT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
file_path = os.path.join(ROOT_DIRECTORY, 'data', 'hollywood.sqlite')

# set the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{file_path}'
app.config['SECRET_KEY'] = 'abc123'

# link the app to the database
# db = SQLAlchemy(app)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
"""
create the database and tables (run this line only once!)
with app.app_context():
    db.create_all()
"""

# create and initialize the SQLiteDataManager instance
DATA_MANAGER = SQLiteDataManager()


def send_movie_recommendations(user_email, recommendations):
    """This function allows the user to send a recommended movie to an email address"""
    msg = Message('Weekly Movie Recommendations', sender='your_email@example.com', recipients=[user_email])
    msg.html = render_template('email/mail_recommendation.html', recommendations=recommendations)
    mail.send(msg)

@app.route('/send_weekly_recommendations')
def send_weekly_recommendations():
    """
    Fetching 12 highest rating movies and send to user by picking user id randomly
    """
    # Retrieve user data
    all_user_ids = [user.id for user in User.query.all()]
    random_user_id = random.choice(all_user_ids)

    user_data = DATA_MANAGER.get_user_data(random_user_id)  # Get a user id randomly
    recommendations = DATA_MANAGER.top_rating_movies()  # recommend by 12 top highest rating movie

    # Send email notifications
    send_movie_recommendations(user_data['email'], recommendations)
    return 'Emails sent successfully!'

@app.route('/api/movies', methods=['GET'])
def movies():
    """
    Retrieve movie information from the data manager and return it as a JSON response.
    Returns:
        jsonify: A JSON response containing user data.
    """
    # Assuming you have a method to fetch user data from the database
    movies_data = DATA_MANAGER.movies()

    # Convert data to JSON format
    movie_list = []
    for movie in movies_data:
       movie_dict = {
           'id': movie.id,
           'title': movie.title,
           'rating': movie.rating,
           'year_release': movie.year_release,
           'director': movie.director,
           'poster': movie.poster
       }
       movie_list.append(movie_dict)

    return jsonify(movie_list)


@app.route('/api/users', methods=['GET'])
def users():
    """
    Retrieve user information from the data manager and return it as a JSON response.
    Returns:
        jsonify: A JSON response containing user data.
    """

    # Assuming you have a method to fetch user data from the database
    user_data = DATA_MANAGER.users()

    # Convert data to JSON format
    user_list = []
    for user in user_data:
        user_dict = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'password': user.password
        }
        user_list.append(user_dict)
    return jsonify(user_list)

@app.route('/api/users', methods=['POST'])
def add_user_api():
    """
    Create a new user based on the provided JSON data.
    Returns:
        jsonify: A JSON response indicating the success or failure of the user creation.
    """
    data = request.get_json()

    # Extract data from the JSON payload
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    user_name = data.get('user_name')
    password = data.get('password')

    # Assuming you have a method to create a new user in your data manager
    success = DATA_MANAGER.add_user(first_name, last_name, email, user_name, password)

    response_data = {'success': success}
    return jsonify(response_data)

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_api(user_id):
    """
    Update an existing user based on the provided JSON data.
    Returns:
        jsonify: A JSON response indicating the success or failure of the user update.
    """
    data = request.get_json()

    # Assuming you have a method to update an existing user in your data manager
    success = DATA_MANAGER.update_user(user_id, data)

    response_data = {'success': success}
    return jsonify(response_data)

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_(user_id):
    """
    Delete an existing user.
    Returns:
        jsonify: A JSON response indicating the success or failure of the user deletion.
    """
    # Assuming you have a method to delete an existing user in your data manager
    success = DATA_MANAGER.delete_user(user_id)  # Replace with your actual method call

    response_data = {'success': success}
    return jsonify(response_data)

@api.route('/api/users/<int:user_id>/movies', methods=['GET'])
def get_user_favorite_movies(user_id):
    """
    List a user's favorite movies.
    Args:
        user_id (int): ID of the user.
    Returns:
        jsonify: A JSON response containing the user's favorite movies.
    """
    user_data = DATA_MANAGER.users()
    user = user_data.get(user_id)
    if user:
        favorite_movies = user.get('favorite_movies', [])
        return jsonify({'favorite_movies': favorite_movies})
    else:
        return jsonify({'message': 'User not found'}), 404

@api.route('/api/users/<int:user_id>/movies', methods=['POST'])
def add_user_favorite_movie(user_id):
    """
    Add a new favorite movie for a user.
    Args:
        user_id (int): ID of the user.
    Returns:
        jsonify: A JSON response indicating the success or failure of adding the movie.
    """
    user_data = DATA_MANAGER.users()
    user = user_data.get(user_id)
    if user:
        data = request.get_json()
        new_favorite_movie = data.get('movie')

        if new_favorite_movie:
            user['favorite_movies'].append(new_favorite_movie)
            return jsonify({'message': 'Movie added to favorites'})
        else:
            return jsonify({'message': 'Invalid data'}), 400
    else:
        return jsonify({'message': 'User not found'}), 404

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """this function asks the user has to be an exist user
    when wanting update or delete existing database"""

    if request.method == 'POST':
        # Get info from the form submission
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            next_url = request.args.get('next')
            print(next_url)
            if not next_url or not next_url.startswith('/'):
                next_url = url_for('home')
            return redirect(next_url)
        else:
            return "Invalid credentials. Please try again."
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/', methods=['GET', 'POST'])
def home():
    """
        This function represents the home page of the website.
        It initializes and renders the content for the home page,
        including any relevant information, links, or images.
        Returns:
        str: The HTML content of the home page.
        """
    # All the exist database: users, movies, directors, stars and genres table
    existing_movies = DATA_MANAGER.movies()
    existing_users = DATA_MANAGER.users()
    existing_directors = DATA_MANAGER.directors()
    existing_genres = DATA_MANAGER.genres()
    existing_stars = DATA_MANAGER.stars()

    # top 12 movies with the highest rating
    top_movies = DATA_MANAGER.top_rating_movies()

    # recommendation movie
    recommendation_movie = DATA_MANAGER.recommendation_movie()

    recommendation_movie_details = data_manager.get_movie_details(recommendation_movie)

    # Determine if dark mode is enabled
    dark_mode_enabled = session.get('dark_mode', False)

    # Searching session
    results = []
    if request.method == 'POST':
        key_word = request.form['key_word_search']
        try:
            if key_word:
                # searching by movie title
                movies_by_title = DATA_MANAGER.movie_by_title(key_word)

                # Searching by movie rating with tolerance=0.1 (only if it's a valid float)
                # movies_by_rating = DATA_MANAGER.movie_by_rating(key_word)

                # Searching by user_first_name
                movies_by_user_first_name = DATA_MANAGER.movies_by_user(key_word)

                # searching by director name
                movies_by_director = DATA_MANAGER.movies_by_director(key_word)

                # searching by star name
                movies_by_star = DATA_MANAGER.movies_by_star(key_word)

                # searching by genre
                movies_by_genre = DATA_MANAGER.movies_by_genre(key_word)

                results = (movies_by_title or
                           movies_by_user_first_name or
                           movies_by_director or
                           movies_by_star or
                           movies_by_genre)
            else:
                flash('Nothing found')
        except Exception:
            print(f"An error occurred during the search")
    return_message = ''
    movie_result_detail = []
    for movie_result in results:
        movie_details = data_manager.get_movie_details(movie_result)
        movie_result_detail.append(movie_details)

    return render_template('home.html', users=existing_users, movies=existing_movies,
                           directors=existing_directors, genres=existing_genres,
                           stars=existing_stars, top_movies=top_movies,
                           dark_mode_class='dark-mode' if dark_mode_enabled else '',
                           recommendation_movie=recommendation_movie,
                           recommendation_movie_details=recommendation_movie_details,
                           search_result=movie_result_detail, return_message=return_message)

@app.route('/toggle_dark_mode', methods=['POST'])
def toggle_dark_mode():
    # Toggle the dark mode status
    session['dark_mode'] = not session.get('dark_mode', False)
    return {'message': 'Dark mode toggled'}

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """This function allows the user to add new user,
    by fining User with first_name, last_name, email, user_name and password accordingly.
    if the email exist, the user has to input another one.
    With all valid, the new user is created and save to SQlite."""
    existing_users = DATA_MANAGER.users()

    # the function to check email if valid
    def in_valid_email(email_input):
        # regular expression pattern to match email addresses
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email_input)

    if request.method == 'POST':
        # get data from form submission
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if in_valid_email(email):
            for user in existing_users:
                if email == user.email and username == user.username:
                    return_message = f'{email} {username} already exist. Please choose another!'
                    return render_template('add_user.html', return_message=return_message)
                else:
                    # add the new user using SQLiteDataManager's add user method
                    DATA_MANAGER.add_user(first_name, last_name, email, username, password)
                    return redirect('/')
        else:
            return_message = 'Email is not valid. Try again.'
            return render_template('add_user.html', return_message=return_message)

    return render_template('add_user.html')

# add movie for the user based on user id
@app.route('/users/<user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """This function allows the user to add a new movie for each user through user_id,
    Each user can create multiple movies. But movies for each user are not duplicated.
    Only the movie title is inputted, and API is called to fetch all the details accordingly.
    With all valid, the movies are created and saved to SQLite."""

    user = User.query.get(user_id)
    existing_movies = DATA_MANAGER.movies()

    # fetching title list of movie exists
    existing_title_list = []
    for movie in existing_movies:
        existing_title_list.append(movie.title)

    if request.method == 'POST':
        # get data from form submission
        title_input = request.form['title']

        favorite = 0
        # checking if exist movie
        if title_input.upper() in existing_title_list:
            return_message = f'Movie was created and belong other user. ' \
                             f'Re-input please!'
            return render_template('add_movie.html', user_id=user_id,
                                   return_message=return_message)
        else:
            # fetching movie details from OMDb API
            url = 'https://www.omdbapi.com/?apikey=99b0f16a&t=' + f'{title_input.lower()}'
            movies_source = requests.get(url)
            movies_source = movies_source.json()
            if movies_source.get("Response") == "True":
                # The tittle is valid
                title = movies_source['Title'].upper()
                year_release = movies_source['Year']
                rating = movies_source['imdbRating']
                director = movies_source['Director'] if movies_source['Director'] != 'N/A' else ''
                poster = movies_source['Poster']
                favorite = favorite if favorite else 0
                genre = movies_source['Genre']
                star = movies_source['Actors']

                # Save movies to database
                DATA_MANAGER.add_movie(title, rating, year_release, director, poster, favorite, user_id)

                # Fetching existing data
                existing_directors = DATA_MANAGER.directors()
                existing_genres = DATA_MANAGER.genres()
                existing_stars = DATA_MANAGER.stars()

                # Find max of existing movies:
                max_movie_id = 0
                for movie in existing_movies:
                    if movie.id > max_movie_id:
                        max_movie_id = movie.id

                current_movie_id = int(max_movie_id) + 1

                # Add director to directors table if not exists
                if director not in [d.name for d in existing_directors]:
                    link = data_manager.get_the_link_for_person(director)
                    DATA_MANAGER.add_director(name=director, link=link, movie_id=current_movie_id)
                else:
                    flash(f'{director} exists in directors!')

                # Split and add stars to stars table if not exists
                for star_name in star.split(','):
                    if star_name.strip() not in existing_stars:
                        link = data_manager.get_the_link_for_person(star_name)
                        DATA_MANAGER.add_star(name=star_name.strip(), link=link, movie_id=current_movie_id)
                    else:
                        flash(f'{star_name.strip()} exists in stars!')

                # Split and add genres to genres table if not exists
                for genre_name in genre.split(','):
                    if genre_name.strip() not in existing_genres:
                        # Instantiate Genre with only the genre name
                        DATA_MANAGER.add_genre(genre=genre_name.strip(), movie_id=current_movie_id)
                    else:
                        flash(f'{genre_name.strip()} exists in genres!')

                return_message = f'Movie {title} was successfully created for user {user_id}!'
                return render_template('add_movie.html', user_id=user_id, user=user,
                                       return_message=return_message)
            else:
                return_message = f'{title_input} is not valid in omdbapi'
                return render_template('add_movie.html', user_id=user_id, user=user,
                                       return_message=return_message)
    return render_template('add_movie.html', user_id=user_id, user=user)

@app.route('/update_movie/<int:id>', methods=['GET', 'POST'])
# @login_required
# Requires the user to be logged in to access this route
def update_movie(id):
    """With each movie_id, the user is able to update the details of movie by new data
    With all valid, new data will be updated of the movie and save back to SQLite.
    Error message will return if id not exist."""

    movie = db.session.get(Movie, id)

    if request.method == 'POST':
        try:
            movie.title = request.form['title']
            movie.rating = float(request.form['rating'])
            movie.year_release = int(request.form['year_release'])
            movie.director = request.form['director']
            movie.favorite = int(request.form['favorite'])

            # Save the changes to the existing database
            db.session.commit()
            return_message = f'Movie {movie.title} was successfully updated!'
            # redirect back to the home page
            return render_template('update_movie.html', movie=movie, return_message=return_message)
        except Exception:
            # Handle the exception
            return_message = 'An error occurred while updating'
            return return_message

    return render_template('update_movie.html', movie=movie)

@app.route('/movie/<int:movie_id>/delete', methods=['GET', 'POST'])
def delete_movie(movie_id):
    """ With the movie id, the user can delete the movie based on the movie id.
        The error message is returned if id is not in existing movie exist."""

    try:
        if request.method == 'POST':
            movie_to_delete = Movie.query.get_or_404(movie_id)
            user_has_other_movies = Movie.query.filter_by(user=movie_to_delete.user).count() > 1
            if user_has_other_movies:
                db.session.delete(movie_to_delete)
                db.session.commit()
            else:
                Movie.query.filter(user=movie_to_delete.user).delete()
                db.session.commit()
        return redirect('/')

    except Exception:
        # Handle the exception
        flash('An error occurred while deleting')
    return redirect('/')

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
# @login_required # Requires the user to be logged in to access this route
def update_user(id):
    """With each user_id, this function allows to update the details of user by new data
    With all valid, new data will be updated of the user and save back to SQLite.
    Error message will return if id not exist."""
    user = db.session.get(User, id)

    if request.method == 'POST':
        try:
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.email = request.form['email']
            user.username = request.form['username']
            user.password = request.form['password']

            # Save the changes to the existing database
            db.session.commit()
            return_message = f'User with ID {id} was successfully updated!'

        except IntegrityError:
            db.session.rollback()
            return_message = 'An integrity error occurred. Please check your input.'
        except ValueError:
            db.session.rollback()
            return_message = 'An error occurred while updating. Please check your input.'
        return render_template('update_user.html', user=user, return_message=return_message)

    return render_template('update_user.html', user=user)


@app.route('/user/<int:id>/delete', methods=['GET', 'POST'])
# @login_required # Requires the user to be logged in to access this route
def delete_user(id):
    """ With the user id, the function allows to delete the user.
        The error message is returned if id is not in existing user exist."""

    try:
        if request.method == 'POST':
            user_to_delete = db.session.get(User, id)

            if user_to_delete:
                db.session.delete(user_to_delete)
                db.session.commit()
                flash(f'user with id: {id} successfully deleted')
            else:
                flash('User not found', 'error')

        return redirect('/')
    except Exception:
        # Handle the exception
        error_message = 'An error occurred while deleting'
        return f'{error_message}'


# Register the api Blueprint with the Flask app
app.register_blueprint(api, url_prefix='/api')

scheduler = BackgroundScheduler()
scheduler.add_job(send_weekly_recommendations, 'interval', weeks=1)  # Send every week
scheduler.start()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=True)
