# python modules import
import os
from datetime import datetime
import random
import string
import json

# Flask modules/funct
from flask import Flask, render_template, abort, request, redirect, url_for,\
                jsonify, flash, make_response
from flask import session as login_session

# Authentication modules/functions
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

# Web modules/functions
import httplib2
import requests
# SQLAlchemy modules/functions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from db.models import Base, User, Category, Item

# initialinsing
from flask import Flask
app = Flask(__name__)

engine = create_engine('sqlite:///db/categorylist.db')
Base.metadata.bind = engine

# create a DBSession instance for reflecting changes to db
DBSession = sessionmaker(bind=engine)
session = DBSession()

# client id retreival
with open('client_secrets.json', 'r') as f:
    client_web_data_json = json.loads(f.read())['web']
    CLIENT_ID = client_web_data_json['client_id']


# API Endpoint for Item
@app.route("/catalog/item/<int:item_id>/JSON")
def itemJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item.serialize)


# login view
@app.route('/login')
def showLogin():
    """
    Show the login page
    """

    if 'gplus_id' in login_session:
        return redirect(url_for('allcategories'))

    # Create anti-forgery state token(csrf token)
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    # storing in  the session for verification ahead
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# google connect method
@app.route('/login/google', methods=['POST'])
def gconnect():
    '''
    Uses google authentication
    '''
    # access token validation
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # retrieving authorization code
    code = request.data

    try:
        # from authorization code into a credential object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # access token validation
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)  # noqa
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # if there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

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
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
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
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/logout')
def logout():
    """
    Log out of current session
    """
    if "gplus_id" in login_session:
        return redirect(url_for('gdisconnect'))
    else:
        return redirect(url_for('showCatalog'))


@app.route('/logout/google')
def gdisconnect():
    """
    Log user out of google plus session
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % credentials
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('allcategories'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser(current_login_session):
    """
    Create New User
    :param current_login_session:
    :return: new user's id
    """
    new_user = User(name=current_login_session['username'],
                    email=current_login_session['email'],
                    profile_pic_url=current_login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(
        email=current_login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# methods for different routes
@app.route("/")
@app.route("/catalog/")
def allcategories():
    '''lists all the categories in the dataabase'''
    categories = session.query(Category).all()
    logged_in_user_id = getUserID(login_session.get('email'))
    recent_items = session.query(Item).order_by("created").limit(3)
    return render_template('all_categories.html', categories=categories,
                           recent_items=recent_items,
                           logged_in_user_id=logged_in_user_id)


@app.route('/catalog/<int:category_id>/')
@app.route('/catalog/<int:category_id>/items/')
def showItemsInCategory(category_id):
    '''shows all items in a given category'''
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        items = session.query(Item).filter_by(category_id=category_id).all()  # noqa
        logged_in_user_id = getUserID(login_session.get('email'))
        categories = session.query(Category).all()
        return render_template('showItemsInCategory.html',
                               category=category, items=items,
                               categories=categories,
                               logged_in_user_id=logged_in_user_id)
    except NoResultFound:
        abort(404)


@app.route('/catalog/<int:item_id>/')
def showItem(item_id):
    '''displays a single item in a category'''
    try:
        logged_in_user_id = getUserID(login_session.get('email'))
        item = session.query(Item).filter_by(id=item_id).one()
        return render_template('showItem.html',
                               item=item,
                               logged_in_user_id=logged_in_user_id)
    except NoResultFound:
        abort(404)


@app.route('/catalog/category/create/', methods=['GET', 'POST'])
def createCategory():
    '''handler for creating new categories'''
    if 'username' not in login_session:
        return redirect('/login')
    logged_in_user_id = getUserID(login_session.get('email'))
    if request.method == 'POST':
        # retreiving form value
        new_category_name = request.form['name'].title()

        try:
            category = session.query(Category).filter_by(name=new_category_name).one()
            msg = "The Category %s already exists" % new_category_name
            return render_template('new_category.html', msg=msg, logged_in_user_id=logged_in_user_id)
        except NoResultFound:
            category = Category(name=new_category_name, user_id=logged_in_user_id)
            session.add(category)
            session.commit()
            return redirect(url_for('allcategories'))
    else:
        return render_template('new_category.html',
                               logged_in_user_id=logged_in_user_id)


@app.route('/catalog/items/create/', methods=['GET', 'POST'])
def createItem():
    '''creating a new item'''
    if 'username' not in login_session:
        return redirect('/login')
    logged_in_user_id = getUserID(login_session.get('email'))
    if request.method == 'POST':

        new_item = Item(name=request.form['name'],
                        description=request.form['description'],
                        category_id=request.form['category_id'],
                        user_id=logged_in_user_id,
                        created=datetime.now())
        session.add(new_item)
        flash('Item %s successfully created' % new_item.name)
        session.commit()
        return redirect(url_for('allcategories'))
    else:
        categories = session.query(Category).all()
        return render_template('new_item.html', categories=categories,
                               logged_in_user_id=logged_in_user_id)


@app.route("/catalog/item/<int:item_id>/edit", methods=['GET', 'POST'])
def editItem(item_id):
    """
    Handles the editing of an item
    """
    if 'username' not in login_session:
        return redirect('/login')

    logged_in_user_id = getUserID(login_session.get('email'))
    edit_item = session.query(Item).filter_by(id=item_id).first()

    if edit_item.user_id != logged_in_user_id:
        flash('You are not authorised to perform this action!')
        return redirect('/')

    if request.method == 'POST':
        edit_item.name = request.form['name']
        edit_item.description = request.form['description']
        edit_item.category_id = request.form['category_id']
        session.add(edit_item)
        session.commit()
        flash('Item %s Successfully Edited' % edit_item.name)
        session.commit()
        return redirect(url_for('allcategories'))
    else:
        categories = session.query(Category).all()
        return render_template('edit_item.html', categories=categories,
                               logged_in_user_id=logged_in_user_id,
                               item=edit_item)


@app.route("/catalog/item/<int:item_id>/delete")
def deleteItem(item_id):
    """
    Handles the deletion of an item
    """
    if 'username' not in login_session:
        return redirect('/login')

    logged_in_user_id = getUserID(login_session.get('email'))
    delete_item = session.query(Item).filter_by(id=item_id).first()

    if delete_item.user_id != logged_in_user_id:
        flash('You are not authorised to perform this action!')
        return redirect('/')

    session.delete(delete_item)
    session.commit()
    flash('Item %s Successfully Deleted' % delete_item.name)
    return redirect('/')


@app.errorhandler(404)
def page_not_found(e):
    '''handler function for status 404'''
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.secret_key = "thisismysupersecret"
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
