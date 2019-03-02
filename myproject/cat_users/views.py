#!/usr/bin/env python3
import random
import string
import json
import httplib2
import requests
from flask import Blueprint, flash, g, redirect, render_template, request, \
    url_for, session as login_session, make_response

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

################
#### config ####
################
from myproject.cat_users.fun import getUserID, createUser

user_blueprint = Blueprint('user', __name__,
                           template_folder='templates')
# Get CLIENT_ID of google sign-in
CLIENT_ID = json.loads(
     open('client_secrets.json', 'r').read())['web']['client_id']
# Get app_id of facebook sign-in
app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
# Get app_secret of facebook sign-in
app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']

################
#### routes ####
################


# show login page
@user_blueprint.route('/login')
def showLogin():
    print("login")
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# login by google account of user
@user_blueprint.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: ' \
              '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# logout google account of user
@user_blueprint.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'))
        response.headers['Content-Type'] = 'application/json'
        return response


# login by facebook account of user
@user_blueprint.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = request.data

    # turn data to string
    access_token = str(access_token)

    # to use access token without (')
    access_token = access_token[access_token.find('\'') + 1:-1]

    print("access token received %s " % access_token)


    url = 'https://graph.facebook.com/oauth/access_token?grant_' \
          'type=fb_exchange_token&client_id={0}&client_secret={1}&fb_exchange_token={2}' \
        .format(app_id, app_secret, access_token)
    h = httplib2.Http()
    result = str(h.request(url, 'GET')[1])

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server 
        token exchange we have to split the token first on commas 
        and select the first index which gives us the key : value
        for the server access token then we split it on colons 
        to pull out the actual token value and replace the remaining 
        quotes with nothing so that it can be used directly 
        in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')
    url = 'https://graph.facebook.com/v2.8/me?' \
          'access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture' \
          '?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: ' \
              '300px;border-radius: 150px;-webkit-border-radius:' \
              ' 150px;-moz-border-radius: 150px;"> '
    # send flash message
    flash("Now logged in as %s" % login_session['username'])
    return output


# logout user's facebook account
@user_blueprint.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?' \
          'access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Disconnect based on provider
@user_blueprint.route('/disconnect')
def disconnect():
    """ Deletes all user session values and redirect to the main page."""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()

        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
            # Reset the user's Facebook session.
            del login_session['username']
            del login_session['email']
            del login_session['picture']

        # Reset the user's session.
        del login_session['user_id']
        del login_session['provider']

        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))
