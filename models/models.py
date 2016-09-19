'''
@author: Harshit Tyagi
Models to create Item Catalog Database schema
'''

# SQLAlchemy packages import==========
from sqlalchemy import Integer, String, DateTime, Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base Class instance
Base = declarative_base()

# Models for the application


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(250), nullable=False)
    name = Column(String(250), nullable=False)
    profile_pic_url = Column(String(250))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
        }


class Category(Base):

    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'user_id': self.user_id,
        }


class Item(Base):

    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    image_url = Column(String(250))
    created = Column(DateTime, nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }

if __name__ == '__main__':
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///categorylist.db')
    Base.metadata.create_all(engine)
