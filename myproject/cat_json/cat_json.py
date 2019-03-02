#!/usr/bin/env python3
from flask import Blueprint, jsonify, request
from flask_restful import Resource, fields

################
#### config ####
################

from module import Category, CatItem
from myproject import session, restplus_api

api_blueprint = Blueprint('api', __name__)


# JSON
# JSON API ENDPOINT HERE TO GET ALL CATEGORIES
# JSON for all categories
# @restplus_api.route('/categories/JSON')
class categoryJSON(Resource):

    def get(self):
        category = session.query(Category).all()
        return {"Categories": [i.serialize for i in category]}


# JSON API ENDPOINT HERE TO GET ALL ITEMS OF ONE CATEGORY
# @restplus_api.route('/categories/<int:category_id>/items/JSON')
class categoryMenuJSON(Resource):

    def get(self, category_id):
        items = session.query(CatItem).filter_by(
            category_id=category_id).all()
        return {"CatItems": [i.serialize for i in items]}


# JSON API ENDPOINT HERE TO GET ONE CATEGORY SPECIFIC ITEM
# @restplus_api.route()
class menuItemJSON(Resource):

    def get(self, category_id, item_id):
        oneItem = session.query(CatItem).filter_by(id=item_id).one()
        return {"CatItem": [oneItem.serialize]}


##
## Actually setup the Api resource routing here
##
restplus_api.add_resource(categoryJSON, '/categories/JSON')
restplus_api.add_resource(categoryMenuJSON, '/categories/<int:category_id>/items/JSON')
restplus_api.add_resource(menuItemJSON, '/categories/<int:category_id>/items/<int:item_id>/JSON')