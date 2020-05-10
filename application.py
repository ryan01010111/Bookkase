import os
import requests

from flask import Flask, session, request, render_template, redirect, json, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import validate_email, login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    
    username = request.form.get("username")
    password = request.form.get("password")

    # ensure user submitted username
    if not username:
        return render_template("index.html", error_message="Please enter a username")
    
    # ensure user submitted password
    if not password:
        return render_template("index.html", error_message="Please enter a password")

    # search for user with submitted username
    user = db.execute("SELECT * FROM users WHERE username = :username",
                        {"username":username}).fetchone()

    # ensure username exists, and password matches
    if not user or not check_password_hash(user.hash, password):
        return render_template("index.html", error_message="Invalid username and/or password")

    # set session for user and log user in
    session['user_id'] = user.id

    return redirect("/")


@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        # ensure user submitted email address
        if not email or not validate_email(email):
            return render_template("register.html", error_message="Please enter a valid email address")

        # ensure user submitted username
        if not username:
            return render_template("register.html", error_message="Please enter a username")

        # ensure username doesn't exist
        checkUsername = db.execute("SELECT * FROM users WHERE username = :username",
                                    {"username":username}).fetchone()
        if checkUsername:
            return render_template("register.html", error_message="That username already exists")
    
        # ensure user submitted password
        if not password:
            return render_template("register.html", error_message="Please enter a password")

        # insert user into users table
        db.execute("INSERT INTO users (email, username, hash) VALUES (:email, :username, :hash)",
                    {"email":email, "username":username, "hash":generate_password_hash(password)})
        db.commit()

        # set session for user and log user in
        user_id = db.execute("SELECT id FROM users WHERE username = :username",
                            {"username":username}).fetchone().id
        session['user_id'] = user_id

        return redirect("/")

    else:

        return render_template("register.html")


@app.route("/book_search")
@login_required
def book_search():

    searchQuery = request.args['q']
    
    results = db.execute("SELECT * FROM books WHERE title ILIKE '%" + searchQuery + "%' OR author ILIKE '%" + searchQuery + "%' OR isbn ILIKE '%" + searchQuery + "%'").fetchall()

    return render_template("book_search.html", searchQuery=searchQuery, results=results)


@app.route("/book/<isbn>")
@login_required
def show_book(isbn):

    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchone()
    bookReviewData = db.execute("SELECT COUNT(*) AS review_count, AVG(reviewrating) AS average_score FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    
    if bookReviewData.review_count:
        ratingData = {
            'reviewCount' : bookReviewData.review_count,
            # convert PostgreSQL's foreign "Decimal" type to float, then round to 1 decimal place
            'average_score' : round(float(bookReviewData.average_score), 1)
        }
    else:
        ratingData = None

    reviews = db.execute("SELECT * FROM reviews INNER JOIN users ON reviews.user_id = users.id WHERE book_isbn = :isbn",
                        {"isbn": isbn}).fetchall()
    checkReviewExists = db.execute("SELECT * FROM reviews INNER JOIN users ON reviews.user_id = users.id WHERE users.id = :user_id AND book_isbn = :isbn",
                                    {"user_id": session['user_id'], "isbn": isbn}).fetchone()
    # api request for Goodreads review/rating data
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.getenv("API_KEY"), "isbns": isbn})
    if res.status_code != 200:
        raise Exception("Error: API request unsuccessful")

    resJson = res.json()
    # take book data (key-value pairs) from first index in list of books
    grData = resJson['books'][0]

    return render_template("book_profile.html", book=book, ratingData=ratingData, reviews=reviews, existingReview=checkReviewExists, grData=grData)


@app.route("/book_review/<isbn>", methods=["POST"])
@login_required
def book_review(isbn):

    reviewRating = int(request.form.get("rating"))
    reviewText = request.form.get("reviewText")

    if not reviewRating or 1 > reviewRating < 6:
        return redirect(f"/book/{isbn}")

    checkReviewExists = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_isbn = :isbn",
                                    {"user_id": session['user_id'], "isbn": isbn}).fetchone()
    if not checkReviewExists:

        db.execute("INSERT INTO reviews (user_id, book_isbn, reviewrating, reviewtext) VALUES (:user_id, :isbn, :reviewrating, :reviewtext)",
                    {"user_id": session['user_id'], "isbn": isbn, "reviewrating": reviewRating, "reviewtext": reviewText})
        db.commit()

    else:

        db.execute("UPDATE reviews SET reviewrating = :reviewrating, reviewtext = :reviewtext WHERE user_id = :user_id AND book_isbn = :isbn",
                    {"reviewrating": reviewRating, "reviewtext": reviewText, "user_id": session['user_id'], "isbn": isbn})
        db.commit()

    return redirect(f"/book/{isbn}")


@app.route("/api")
def api_about():

    return render_template("api_about.html")


@app.route("/api/books/<isbn>")
def book_api(isbn):

    bookInfo = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    # ensure book is in database
    if bookInfo is None:
        return jsonify({"error": "ISBN not found"}), 404

    bookReviewData = db.execute("SELECT COUNT(*) AS review_count, AVG(reviewrating) AS average_score FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    if bookReviewData.review_count:
        # convert PostgreSQL's foreign "Decimal" type to float, then round to 1 decimal place
        average_score = round(float(bookReviewData.average_score), 1)
    else:
        average_score = None

    return jsonify({
        
        "isbn": isbn,
        "title": bookInfo.title,
        "author": bookInfo.author,
        "year_published": bookInfo.year,
        "review_count": bookReviewData.review_count,
        "average_score": average_score
    })
    

