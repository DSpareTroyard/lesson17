# app.py

from flask import Flask, request, render_template, make_response
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 2}
db = SQLAlchemy(app)


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class MovieSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()
    director_name = fields.Str()
    genre_name = fields.Str()


class DirectorSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class GenreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


api = Api(app)

movie_ns = api.namespace("movies")
director_ns = api.namespace("directors")
genre_ns = api.namespace("genres")

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)

genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)


@movie_ns.route("/")
class MoviesView(Resource):
    def get(self):
        p = request.args.get("p")
        did = request.args.get("director_id")
        gid = request.args.get("genre_id")

        headers = {'Content-Type': 'text/html'}
        if not p:
            p = 0
            page = 1
        else:
            page = p
            p = (int(p) - 1) * 5

        if not (did or gid):
            movies = db.session.query(Movie.id, Movie.title, Movie.description,
                                      Movie.trailer, Movie.year, Movie.director_id,
                                      Movie.rating, Movie.genre_id,
                                      Director.name.label("director_name"),
                                      Genre.name.label("genre_name")).join(Director, Genre).filter(
                Director.id == Movie.director_id and
                Genre.id == Movie.genre_id).offset(p).limit(5).all()

            return make_response(render_template("movies.html",
                                                 movies_info=movies_schema.dump(movies),
                                                 page=page), 200, headers)

        elif did and gid:
            movies = db.session.query(Movie.id, Movie.title, Movie.description,
                                      Movie.trailer, Movie.year, Movie.director_id,
                                      Movie.rating, Movie.genre_id,
                                      Director.name.label("director_name"),
                                      Genre.name.label("genre_name")).join(Director, Genre).filter(
                Movie.genre_id == gid).filter(Movie.director_id == did and
                                              Director.id == Movie.director_id and
                                              Genre.id == Movie.genre_id).offset(p).limit(5).all()

            return make_response(render_template("movies.html",
                                                 movies_info=movies_schema.dump(movies),
                                                 page=page,
                                                 genre_id=gid,
                                                 director_id=did), 200, headers)

        elif did:
            movies = db.session.query(Movie.id, Movie.title, Movie.description,
                                      Movie.trailer, Movie.year, Movie.director_id,
                                      Movie.rating, Movie.genre_id,
                                      Director.name.label("director_name"),
                                      Genre.name.label("genre_name")).join(Director, Genre).filter(
                Movie.director_id == did and
                Director.id == Movie.director_id and
                Genre.id == Movie.genre_id).offset(p).limit(5).all()

            return make_response(render_template("movies.html",
                                                 movies_info=movies_schema.dump(movies),
                                                 page=page,
                                                 director_id=did), 200, headers)

        elif gid:
            movies = db.session.query(Movie.id, Movie.title, Movie.description,
                                      Movie.trailer, Movie.year, Movie.director_id,
                                      Movie.rating, Movie.genre_id,
                                      Director.name.label("director_name"),
                                      Genre.name.label("genre_name")).join(Director, Genre).filter(
                Movie.genre_id == gid and
                Director.id == Movie.director_id and
                Genre.id == Movie.genre_id).offset(p).limit(5).all()

            return make_response(render_template("movies.html",
                                                 movies_info=movies_schema.dump(movies),
                                                 page=page,
                                                 genre_id=gid), 200, headers)

    def post(self):
        req_json = request.json
        new_movie = Movie(**req_json)
        with db.session.begin():
            db.session.add(new_movie)
        return "", 201


@movie_ns.route("/<int:mid>/")
class MovieView(Resource):
    def get(self, mid):
        if not Movie.query.get(mid):
            return "", 404

        movie = db.session.query(Movie.id, Movie.title, Movie.description,
                                 Movie.trailer, Movie.year, Movie.director_id,
                                 Movie.rating, Movie.genre_id,
                                 Director.name.label("director_name"),
                                 Genre.name.label("genre_name")).join(Director, Genre).filter(
            Movie.id == mid and Director.id == Movie.director_id and Genre.id == Movie.genre_id).first()
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template("movie.html",
                                             movie=movie_schema.dump(movie)), 200, headers)

    def put(self, mid):
        if not Movie.query.get(mid):
            return "", 404

        movie = Movie.query.get(mid)
        req_json = request.json
        movie.title = req_json['title']
        movie.description = req_json['description']
        movie.trailer = req_json['trailer']
        movie.year = req_json['year']
        movie.rating = req_json['rating']
        movie.genre_id = req_json['genre_id']
        movie.director_id = req_json['director_id']

        db.session.add(movie)
        db.session.commit()

        return "", 204

    def patch(self, mid):
        if not Movie.query.get(mid):
            return "", 404

        movie = Movie.query.get(mid)
        req_json = request.json

        if "title" in req_json:
            movie.title = req_json['title']
        if "description" in req_json:
            movie.description = req_json['description']
        if "trailer" in req_json:
            movie.trailer = req_json['trailer']
        if "year" in req_json:
            movie.year = req_json['year']
        if "rating" in req_json:
            movie.rating = req_json['rating']
        if "genre_id" in req_json:
            movie.genre_id = req_json['genre_id']
        if "director_id" in req_json:
            movie.director_id = req_json['director_id']

        db.session.add(movie)
        db.session.commit()

        return "", 204

    def delete(self, mid):
        if not Movie.query.get(mid):
            return "", 404

        movie = Movie.query.get(mid)
        db.session.delete(movie)
        db.session.commit()

        return "", 204


@director_ns.route("/")
class DirectorsView(Resource):
    def get(self):
        directors = Director.query.all()
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template("directors.html",
                                             directors=directors_schema.dump(directors)), 200, headers)

    def post(self):
        req_json = request.json
        new_dir = Director(**req_json)
        with db.session.begin():
            db.session.add(new_dir)
        return "", 201


@director_ns.route("/<int:did>/")
class DirectorView(Resource):
    def get(self, did):
        if not Director.query.get(did):
            return "", 404
        director = Director.query.get(did)
        movies = db.session.query(Movie).filter(Movie.director_id == did).all()
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template("director.html",
                                             director=director_schema.dump(director),
                                             movies=movies_schema.dump(movies)),
                             200, headers)

    def put(self, did):
        if not Director.query.get(did):
            return "", 404

        director = Director.query.get(did)
        req_json = request.json
        director.name = req_json['name']
        db.session.add(director)
        db.session.commit()

        return "", 204

    def delete(self, did):
        if not Director.query.get(did):
            return "", 404

        director = Director.query.get(did)
        db.session.delete(director)
        db.session.commit()

        return "", 204


@genre_ns.route("/")
class GenresView(Resource):
    def get(self):
        genres = Genre.query.all()
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template("genres.html",
                                             genres=genres_schema.dump(genres)),
                             200, headers)

    def post(self):
        req_json = request.json
        new_genre = Genre(**req_json)
        with db.session.begin():
            db.session.add(new_genre)
        return "", 201


@genre_ns.route("/<int:gid>/")
class GenreView(Resource):
    def get(self, gid):
        if not Genre.query.get(gid):
            return "", 404
        genre = Genre.query.get(gid)
        movies = db.session.query(Movie).filter(Movie.genre_id == gid).all()
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template("genre.html",
                                             genre=genre_schema.dump(genre),
                                             movies=movies_schema.dump(movies)),
                             200, headers)

    def put(self, gid):
        if not Genre.query.get(gid):
            return "", 404
        genre = Genre.query.get(gid)
        req_json = request.json
        genre.name = req_json['name']
        db.session.add(genre)
        db.session.commit()

        return "", 204

    def delete(self, gid):
        if not Genre.query.get(gid):
            return "", 404

        genre = Genre.query.get(gid)
        db.session.delete(genre)
        db.session.commit()

        return "", 204


if __name__ == '__main__':
    app.run(debug=True)
