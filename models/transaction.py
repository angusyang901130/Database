from db import db
from datetime import datetime
from babel.dates import format_datetime

class TransactionModel(db.Model):
    __tablename__ = 'Transactions'
    _id = db.Column('id', db.Integer, primary_key=True)
    transactionType = db.Column('transactionType', db.String(50), nullable=False)
    transactionTime = db.Column('transactionTime', db.DateTime)
    moneyChange = db.Column('moneyChange', db.String)
    transactionTrader = db.Column('transactionTrader', db.String) # if it is user, save 'user account'

    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    # users = db.relationship('UserModel', backref='shopkeeper')

    def __init__ (self, transactionType, moneyChange, transactionTrader, user_id):
        self.transactionType = transactionType
        dt = datetime.now()
        format_datetime(dt)
        self.transactionTime = dt
        self.moneyChange = moneyChange
        self.transactionTrader = transactionTrader
        self.user_id = user_id
    
    def json(self):
        return {'name': self.shopName, 'items': [item.json() for item in self.items.all()]}
    
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
    
    @classmethod
    def find_by_userId(cls, userId):
        return cls.query.filter_by(user_id=userId).all()