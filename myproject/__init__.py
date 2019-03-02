#!/usr/bin/env python3

from flask import Flask, render_template, url_for
from redis import Redis
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_restful import Api

from module import Category, CatItem, Base

app = Flask(__name__)
restplus_api = Api(app)


auth = HTTPBasicAuth()
redis = Redis()

# Connect to database
engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False},
                       echo=True)

Base.metadata.bind = engine

# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()

from myproject.catalogs.views import catlog_blueprint
from myproject.cat_users.views import user_blueprint
from myproject.cat_json.cat_json import api_blueprint

app.register_blueprint(catlog_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(api_blueprint)


# Show all categories
@app.route('/')
@app.route('/home')
@app.route('/categories')
def showCategories():
    categories = session.query(Category).all()
    # Get category items added
    items = session.query(CatItem).all()
    return render_template('publicCategories.html',
                           categories=categories, items=items)
