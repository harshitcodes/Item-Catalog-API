from datetime import datetime

# sqlalchemy modules/functions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# project models
from models import Base, User, Category, Item

# create engine to existing db and bind to it
engine = create_engine('sqlite:///categorylist.db')
Base.metadata.bind = engine

# create a DBSession instance for reflecting changes to db
DBSession = sessionmaker(bind=engine)
session = DBSession()

# methods to populate the Database


def addUser(email, name, pic_url):
    '''add a category to the db'''
    user = User(email=email, name=name, profile_pic_url=pic_url)
    session.add(user)
    session.commit()
    print "added user: {}".format(user.id)
    return user


def addCategory(name, user_id):
    '''add a category to the db'''
    category = Category(name=name, user_id=user_id)
    session.add(category)
    session.commit()
    print 'added category: %s' % category.id
    return category


def addItem(name, description, category, user_id):
    '''add an item to the db'''
    item = Item(name=name, description=description, category=category,
                created=datetime.utcnow(), user_id=user_id)
    session.add(item)
    session.commit()
    print 'added item: %s' % item.id
    return item

print

# delete all data in the db first
session.query(User).delete()
session.query(Category).delete()
session.query(Item).delete()
print 'deleted all data in db'
print

# add test user
user1 = addUser('test@test.com', 'The One', 'test.png')
print

# add test categories
baseball = addCategory('Baseball', 1)
hockey = addCategory('Hockey', 1)
snowboarding = addCategory('Snowboarding', 1)
soccer = addCategory('Soccer', 1)
print

# add test items
addItem('Bat', 'Really cool baseball bat', baseball, 1)
addItem('Goggles', 'Protect your eyes with these goggles', snowboarding, 1)
addItem('Snowboard', 'Cool snowboard', snowboarding, 1)
addItem('Shinguards', 'Protect your shins with these guards', soccer, 1)
addItem('Jersey', 'Look like a pro with this jersey', soccer, '')
print

# display current state of the db as a sanity check
print 'Users in db:'
users = session.query(User).all()
for user in users:
    print 'email=%s, name=%s, picture=%s' % (`user.email`, `user.name`, `user.profile_pic_url`)
print
print 'Categories in db:'
categories = session.query(Category).all()
for category in categories:
    print 'name=%s, creator_email=%s' % (`category.name`, `str(category.user_id)`)
print
print 'Items in db:'
items = session.query(Item).all()
for item in items:
    print 'name=%s, description=%s, category_name=%s, creation_time=%s, user_id=%s' % (`item.name`, `item.description`, `item.category.name`, `item.created`, `item.user_id`)
print