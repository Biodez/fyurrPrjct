#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from datetime import datetime
from os import abort
import sys
from typing import final
from itsdangerous import exc
from pytz import timezone
from email.policy import default
import json
import dateutil.parser
import babel
from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import ForeignKey, distinct
from forms import *
from flask_migrate import Migrate;
import collections
collections.Callable = collections.abc.Callable
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
tz = timezone('EST')


# TODO: connect to a local postgresql database
migrate = Migrate(app, db);

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, default=False);
    seeking_description = db.Column(db.String(120), nullable=False);
    website = db.Column(db.String(120));
    shows = db.relationship('Show', backref='venue', lazy=True);
    genres = db.relationship("Venue_Genre", passive_deletes=True, backref="venue", lazy=True);

    def __repr__(self):
        return f'< Venue {self.city} {self.state} >'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    shows = db.relationship('Show', backref='artist', lazy=True);
    seeking_venue = db.Column(db.Boolean, default=False);
    seeking_description = db.Column(db.String(120));
    website = db.Column(db.String(120));
    genres = db.relationship("Artist_Genre", passive_deletes=True, backref="artist", lazy=True);

    def __repr__(self):
        return f'< Artist {self.name} {self.genre} >'

    

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key=True);
  show_start_time = db.Column(db.DateTime, nullable=False, default=datetime.now(tz));
  artist_id = db.Column(db.Integer, ForeignKey('artist.id'), nullable=False);
  venue_id = db.Column(db.Integer, ForeignKey('venue.id'), nullable=False);

  def __repr__(self):
      return f'< Show {self.artist_id} {self.venue_id} >'

class Venue_Genre(db.Model):
  __tablename__ = 'venue_genres';
  id = db.Column(db.Integer, primary_key=True);
  genre = db.Column(db.String(30), nullable=False);
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'), nullable=False);

  def __repr__(self):
      return f'< venue genre {self.genre} {self.venue_id} >'

class Artist_Genre(db.Model):
  __tablename__ = 'artist_genres';
  id = db.Column(db.Integer, primary_key=True);
  genre = db.Column(db.String(30), nullable=False);
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'), nullable=False);

  def __repr__(self):
      return f'< artist genre {self.genre} {self.artist_id} >'

# db.create_all();
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  present_date = datetime.now();
  data = [];
  # num_upcoming_shows = 0;
  locations = db.session.query(distinct(Venue.city), Venue.state).all();
  for location in locations:
    city = location[0];
    state = location[1];

    location_list = {
      "city" : city,
      "state" : state,
      "venues" : []
    }

    venues = Venue.query.filter_by(city=city, state=state).all();
    for venue in venues:
      venue_id = venue.id;
      venue_name = venue.name;

      num_upcoming_shows = Show.query.filter_by(venue_id=venue_id).filter(Show.show_start_time > present_date).all();

      venue_sub_list = {
        "id" : venue_id,
        "name" : venue_name,
        "num_upcoming_shows" : num_upcoming_shows
      }

      # print(venue_sub_list);

      location_list["venues"].append(venue_sub_list);

      # print(location_list)

    data.append(location_list);
    # print(data)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get("search_term", "");
  venues_result = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all() #This will return a list of venues 
  list_of_venues = [];
  present_date = datetime.now()
  for venue in venues_result:
    show_venue = Show.query.filter_by(venue_id = venue.id);
    num_upcoming_shows = 0;
    for show in show_venue:
      if show.show_start_time > present_date:
        num_upcoming_shows += 1;
    list_of_venues.append({
      "id" : venue.id,
      "name" : venue.name,
      "num_upcoming_shows" : num_upcoming_shows
    })

  response = {
    "count" : len(venues_result),
    "data" : list_of_venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = {}

  venue = Venue.query.get(venue_id);
  present_date = datetime.now();
  past_shows = [];
  past_shows_count = 0;
  upcoming_shows = [];
  upcoming_shows_count = 0;

  for genre in venue.genres:
    genre_name = genre.genre

  for show in venue.shows:
    artist = Artist.query.get(show.artist_id)
    if show.show_start_time >= present_date:
      upcoming_shows_count += 1
      upcoming_shows.append({
        "artist_id" : artist.id,
        "artist_name" : artist.name,
        "artist_image_link" : artist.image_link,
        "start_time" : format_datetime(str(show.show_start_time))
      })
    elif show.show_start_time < present_date:
      past_shows_count += 1
      past_shows.append({
        "artist_id" : artist.id,
        "artist_name" : artist.name,
        "artist_image_link" : artist.image_link,
        "start_time" : format_datetime(str(show.show_start_time))
      })
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": genre_name,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": upcoming_shows_count
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  error = False;
  try:
    name = request.form.get('name');
    city = request.form.get('city');
    state = request.form.get('state');
    address = request.form.get('address');
    phone = request.form.get('phone');
    genres = request.form.getlist('genres');
    facebook_link = request.form.get('facebook_link');
    seeking_talent = True if request.form.get('seeking_talent') == 'y' else False;
    seeking_description = request.form.get('seeking_description');
    website = request.form.get('website');
    image_link = request.form.get('image_link');

    new_venue = Venue(
      name = name,
      city = city,
      state = state,
      address = address,
      phone = phone,
      facebook_link = facebook_link,
      seeking_talent = seeking_talent,
      seeking_description = seeking_description,
      website = website,
      image_link = image_link
    );
    for genre in genres:
      get_genre = Venue_Genre.query.filter_by(genre=genre).one_or_none();
      if get_genre:
        new_venue.genres.append(get_genre)
      else:
       curr_genre = Venue_Genre(genre=genre);
       db.session.add(curr_genre);
       new_venue.genres.append(curr_genre)
    db.session.add(new_venue);
    db.session.commit();
    # db.session.refresh(new_venue);
    flash('Venue ' + request.form.get("name") + ' was successfully listed!')
    print(new_venue);
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    db.session.rollback();
    error = True
    print(sys.exc_info())
    flash(f'Error occured while trying to list the venue with name : {request.form.get("name")}');
  finally:
    db.session.close()
    return render_template('pages/home.html')
  # if not error:
  #   flash('Venue ' + request.form.get("name") + ' was successfully listed!')
  #   return render_template('pages/home.html')
  # else:
  #   flash(f'Error occured while trying to list the venue with name : {request.form.get("name")}');
  #   # abort(500);

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  delete_venue = Venue.query.get(venue_id).name;

  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash(f'{delete_venue} was successfully deleted...')
  except:
    db.session.rollback()
    return jsonify({
      "errorMessage" : f"{delete_venue} was not successfully deleted from db"
    })
  finally:
    db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.order_by(Artist.name).all()

  data = []
  for artist in artists:
      data.append({
          "id": artist.id,
          "name": artist.name
      })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get("search_term", "");
  artist_result = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all() #This will return a list of venues 
  list_of_artist = [];
  present_date = datetime.now()
  for artist in artist_result:
    show_artist = Show.query.filter_by(venue_id = artist.id);
    num_upcoming_shows = 0;
    for show in show_artist:
      if show.show_start_time > present_date:
        num_upcoming_shows += 1;
    list_of_artist.append({
      "id" : artist.id,
      "name" : artist.name,
      "num_upcoming_shows" : num_upcoming_shows
    })

  response = {
    "count" : len(artist_result),
    "data" : list_of_artist
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  data = {}

  artist = Artist.query.get(artist_id);
  present_date = datetime.now();
  past_shows = [];
  past_shows_count = 0;
  upcoming_shows = [];
  upcoming_shows_count = 0;

  for genre in artist.genres:
    genre_name = genre.genre

  for show in artist.shows:
    venue = Venue.query.get(show.venue_id)
    if show.show_start_time >= present_date:
      upcoming_shows_count += 1
      upcoming_shows.append({
        "venue_id" : venue.id,
        "venue_name" : venue.name,
        "venue_image_link" : venue.image_link,
        "start_time" : format_datetime(str(show.show_start_time))
      })
    elif show.show_start_time < present_date:
      past_shows_count += 1
      past_shows.append({
        "venue_id" : venue.id,
        "venue_name" : venue.name,
        "venue_image_link" : venue.image_link,
        "start_time" : format_datetime(str(show.show_start_time))
      })
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": genre_name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": upcoming_shows_count
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id);
  form = ArtistForm(obj=artist)
  genres = []
  if len(artist.genres) > 0:
    for genre in artist.genres:
      genres.append(genre);
  data = {
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": genres,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get(artist_id);

    name = request.form.get("name");
    city = request.form.get("city");
    state = request.form.get("state");
    phone = request.form.get("phone");
    genres = request.form.getlist("genres");
    seeking_venue = True if request.form.get("seeking_venue") == 'y' else False
    seeking_description = request.form.get("seeking_description")
    image_link = request.form.get("image_link");
    website = request.form.get("website")
    facebook_link = request.form.get("facebook_link");

    artist.name = name
    artist.city = city
    artist.state = state
    artist.phone = phone
    artist.facebook_link = facebook_link
    artist.seeking_venue = seeking_venue
    artist.seeking_description = seeking_description
    artist.image_link = image_link
    artist.website = website

    artist_genre = []
    for genre in genres:
      curr_genre = Artist_Genre(genre=genre);
      curr_genre.artist = artist
      artist_genre.append(curr_genre)

    db.session.add(artist)
    db.session.commit()
    db.session.refresh(artist)
    flash(f"Artist was updated successfully")
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>
  venue = {}
  try:
    venue_request = Venue.query.get(venue_id);
    form = VenueForm(obj=venue_request)
    if venue_request is None:
      return not_found_error(404)
    
    venue_genre = []
    if (len(venue_request.genres) > 0):
      for genre in venue_request.genres:
        venue_genre.append(genre)
    venue = {
      "id":venue_request.id,
      "name":venue_request.name,
      "genres":venue_genre,
      "address":venue_request.address,
      "city": venue_request.city,
      "state": venue_request.state,
      "phone": venue_request.phone,
      "website": venue_request.website,
      "facebook_link": venue_request.facebook_link,
      "seeking_talent": venue_request.seeking_talent,
      "seeking_description": venue_request.seeking_description,
      "image_link": venue_request.image_link
    }
  except:
    flash("request is not successfull...");
    print(sys.exc_info());
    return redirect(url_for("index"));
  finally:
    db.session.close();
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()
  try:

    update_venue = Venue.query.get(venue_id)

    name = request.form.get('name');
    city = request.form.get('city');
    state = request.form.get('state');
    address = request.form.get("address")
    phone = request.form.get('phone');
    genres = request.form.getlist('genres');
    facebook_link = request.form.get('facebook_link');
    seeking_talent = True if request.form.get('seeking_talent') == 'y' else False;
    seeking_description = request.form.get('seeking_description');
    website = request.form.get('website');
    image_link = request.form.get('image_link');

    update_venue.name = name
    update_venue.city = city
    update_venue.state = state
    update_venue.address = address
    update_venue.phone = phone
    update_venue.facebook_link = facebook_link
    update_venue.seeking_talent = seeking_talent
    update_venue.seeking_description = seeking_description
    update_venue.website = website
    update_venue.image_link = image_link

    venue_genre = []
    for genre in genres:
      curr_genre = Venue_Genre(genre = genre)
      curr_genre.venue = update_venue
      venue_genre.append(curr_genre)
    db.session.add(update_venue)
    db.session.commit()
    db.session.refresh(update_venue)
    flash("venue was updated successfully...")
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False;
  try:
    name = request.form.get('name');
    city = request.form.get('city');
    state = request.form.get('state');
    phone = request.form.get('phone');
    genres = request.form.getlist('genres');
    facebook_link = request.form.get('facebook_link');
    seeking_venue = True if request.form.get('seeking_venue') == 'y' else False;
    seeking_description = request.form.get('seeking_description');
    website = request.form.get('website');
    image_link = request.form.get('image_link');

    new_artist = Artist(
      name = name,
      city = city,
      state = state,
      phone = phone,
      facebook_link = facebook_link,
      seeking_venue = seeking_venue,
      seeking_description = seeking_description,
      website = website,
      image_link = image_link
    );
    for genre in genres:
      get_genre = Artist_Genre.query.filter_by(genre=genre).one_or_none();
      if get_genre:
        new_artist.genres.append(get_genre)
      else:
       curr_genre = Artist_Genre(genre=genre);
       db.session.add(curr_genre);
       new_artist.genres.append(curr_genre)
    db.session.add(new_artist);
    db.session.commit();
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    db.session.rollback();
    error = True
    print(sys.exc_info())
    flash(f'Error occured while trying to list the venue with name : {request.form.get("name")}');
  finally:
    db.session.close()
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  shows = Show.query.all();

  for show in shows:
    data.append({
      "venue_id" : show.venue.id,
      "venue_name" : show.venue.name,
      "artist_id" : show.artist.id,
      "artist_name" : show.artist.name,
      "artist_image_link" : show.artist.image_link,
      "start_time" : format_datetime(str(show.show_start_time))
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False;
  try:
    show_start_time = request.form.get('show_start_time');
    artist_id = request.form.get("artist_id");
    venue_id = request.form.get("venue_id");

    check_artist = Artist.query.get(artist_id)
    check_venue = Venue.query.get(venue_id)

    if check_artist is None or check_venue is None:
      error = True
    
    if check_artist is not None and check_venue is not None:
      new_show = Show(
        show_start_time = show_start_time,
        artist_id = artist_id,
        venue_id = venue_id
      );
      db.session.add(new_show);
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
  except:
    db.session.rollback();
    print(sys.exc_info())
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close();
  if error is True:
    f'There is no record with either artist id {request.form.get("artist_id")} or venue id {request.form.get("venue_id")}'
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
