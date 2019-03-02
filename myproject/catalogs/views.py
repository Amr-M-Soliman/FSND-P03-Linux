#!/usr/bin/env python3

from flask import Blueprint, flash, g, redirect, render_template, \
    request, url_for, session as login_session

from module import Category, CatItem

################
#### config ####
################
from myproject import session
from myproject.cat_users.fun import getUserInfo
from myproject.cat_users.views import user_blueprint

catlog_blueprint = Blueprint('catalog', __name__,
                             template_folder='templates')


################
#### routes ####
################

# Show all items of the selected category
@catlog_blueprint.route('/categories/<int:category_id>/items')
def showCategory(category_id):
    # Get all categories
    categories = session.query(Category).all()

    # Get category
    category = session.query(Category).filter_by(id=category_id).first()

    # Get name of category
    categoryName = category.name

    # Get all items of a specific category
    categoryItems = session.query(CatItem) \
        .filter_by(category_id=category_id).all()

    # Get count of category items
    categoryItemsCount = session.query(CatItem) \
        .filter_by(category_id=category_id).count()

    return render_template('category.html',
                           categories=categories,
                           categoryItems=categoryItems,
                           categoryName=categoryName,
                           categoryItemsCount=categoryItemsCount)


# Create a new category
@catlog_blueprint.route('/category/new', methods=['GET', 'POST'])
@user_blueprint.route('/login')
def newCategory():
    # POST method
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'],
                               user_id=login_session['user_id'])

        # Add the created category to the database
        session.add(newCategory)
        session.commit()

        # Send a flah message
        flash("New Category created!")

        # Redirect to 'showCategories' page
        return redirect(url_for('showCategories'))

    else:

        # Return the page to create a new category
        return render_template('newCategories.html')


# Update a category
@catlog_blueprint.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@user_blueprint.route('/login')
def editCategory(category_id):
    # Get the specific category to be updated by user
    categoryToEdit = session.query(
        Category).filter_by(id=category_id).one()

    # If logged in user != item owner redirect them
    if categoryToEdit.user_id != login_session['user_id']:
        return "<script>function myFunction()" \
               " {alert('You are not authorized to edit this category." \
               " Please create your own category in order to edit.');}" \
               "</script><body onload='myFunction()''>"

    # POST method
    if request.method == 'POST':
        if request.form['name']:
            categoryToEdit.name = request.form['name']

            # Sen a flash message
            flash("Category Edited!")

            # Redirect the user to 'showCategories' page
            return redirect(url_for('showCategories'))
    else:

        # The page to update the category
        return render_template(
            'editCategory.html', category=categoryToEdit)


# Delete a category
@catlog_blueprint.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
@user_blueprint.route('/login')
def deleteCategory(category_id):
    # Get the specific category to be deleted by user
    categoryToDelete = session.query(
        Category).filter_by(id=category_id).one()

    # Git all category items to be deleted
    itemsToDelete = session.query(CatItem). \
        filter_by(category_id=category_id).all()

    # If logged in user != item owner redirect them
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction()" \
               " {alert('You are not authorized to delete this category.');}" \
               "</script><body onload='myFunction()''>"

    # POST methods
    if request.method == 'POST':

        # Delete all items in category
        for i in itemsToDelete:
            session.delete(i)

        # Delete category
        session.delete(categoryToDelete)
        session.commit()

        # Send flash message
        flash("A category has deleted!")

        # Redirect the user to 'showCategories' page
        return redirect(
            url_for('showCategories'))
    else:
        # The page to delete the category
        return render_template(
            'deleteCategory.html', category=categoryToDelete)


# Show an item
@catlog_blueprint.route('/categories/<int:category_id>/items/<int:item_id>')
def showItem(category_id, item_id):
    # Get the specific item by item_id
    item = session.query(CatItem).filter_by(id=item_id).first()

    # Get the creator id of the item
    creator = getUserInfo(item.user_id)
    return render_template('categoryItem.html',
                           item=item, creator=creator)


# Create a new item
@catlog_blueprint.route('/category/newitem', methods=['GET', 'POST'])
@user_blueprint.route('/login')
def newItem():
    # POST method
    if request.method == 'POST':
        newItem = CatItem(name=request.form['name'],
                          description=request.form['description'],
                          category_id=request.form['category'],
                          user_id=login_session['user_id'])

        # Add the new item to database
        session.add(newItem)
        session.commit()

        # Send a slush message
        flash("New Game created!")

        # Redirect to the main page
        return redirect(url_for('showCategories'))
    else:

        # Get all categories
        categories = session.query(Category).all()

        # Return the page to create new item
        return render_template('newmenuitem.html', categories=categories)


# Update an item
@catlog_blueprint.route('/category/<int:category_id>/item/<int:item_id>/edit:',
                        methods=['GET', 'POST'])
@user_blueprint.route('/login')
def editItem(category_id, item_id):

    # Get the item to be updated by item_id
    itemTOEdit = session.query(CatItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()

    # If logged in user != item owner redirect them
    if login_session['user_id'] != itemTOEdit.user_id:
        return "<script>function myFunction()" \
               "{alert('You are not authorized to add items to this category." \
               " Please create your own category in order to add items.');}" \
               "</script><body onload='myFunction()''>"

    # POST methods
    if request.method == 'POST':
        if request.form['name']:
            itemTOEdit.name = request.form['name']
        if request.form['description']:
            itemTOEdit.description = request.form['description']
        if request.form['category']:
            itemTOEdit.category_id = request.form['category']

        # Update the item
        session.add(itemTOEdit)
        session.commit()

        # Send a flash message
        flash("Game edited!")

        # Redirect the user to 'showItem'
        return redirect(url_for('catalog.showItem',
                                category_id=category_id,
                                item_id=item_id))
    else:

        # The page to update the item
        return render_template(
            'editmenuitem.html', category_id=category_id,
            item_id=item_id,
            item=itemTOEdit,
            categories=categories)


# Delete an item
@catlog_blueprint.route('/category/<int:category_id>/item/<int:item_id>/delete',
                        methods=['GET', 'POST'])
@user_blueprint.route('/login')
def deleteItem(category_id, item_id):

    # Get the item to be deleted by item_id
    itemToDelete = session.query(CatItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()

    # If logged in user != item owner redirect them
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction()" \
               "{alert('You are not authorized to delete items to this category." \
               " Please create your own category in order to delete items.');}" \
               "</script><body onload='myFunction()''>"

    # POST method
    if request.method == 'POST':

        # Delete the item from database
        session.delete(itemToDelete)
        session.commit()

        # Send a flash message
        flash('Item deleted')

        # Redirect the user to 'showCategory' page
        return redirect(url_for('catalog.showCategory', category_id=category_id))
    else:

        # The page to delete the item
        return render_template('deleteMenuItem.html', item=itemToDelete)
