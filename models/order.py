from db import db
from datetime import datetime
from babel.dates import format_datetime

class OrderModel(db.Model):
    __tablename__ = 'Orders'
    _id = db.Column('id', db.Integer, primary_key=True)
    orderState = db.Column('orderState', db.String(10), nullable=False)
    orderStart = db.Column('orderStart', db.DateTime)
    orderEnd = db.Column('orderEnd', db.DateTime)
    orderPrice = db.Column('orderPrice', db.Integer)
    shopName = db.Column('shopName', db.String(50), nullable=False)
    orderDetails = db.Column('orderDetails', db.String, nullable=False)

    #### shop && user relation
    shop_id = db.Column(db.Integer, db.ForeignKey('Shops.id'))
    shop = db.relationship('ShopModel', backref='Orders')

    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    shop = db.relationship('UserModel', backref='Orders')

    def __init__(self, orderState, orderPrice, shop_id, user_id, shopName, orderDetails):
        self.orderState = orderState
        # self.orderStart = orderStart
        self.orderEnd = None
        self.orderPrice = orderPrice
        self.shop_id = shop_id
        self.user_id = user_id
        dt = datetime.now()
        format_datetime(dt)
        self.orderStart = dt
        #print(dt)
        self.shopName = shopName
        self.orderDetails = orderDetails

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def modify_from_db(self, orderState):
        try:
            dt = datetime.now()
            format_datetime(dt)
            self.orderState = orderState
            self.orderEnd = dt
            db.session.commit()
            return {'message': 'Order has been modified!!'}
        except:
            return {'message': 'Error during modifying order!!'}

    @classmethod
    def find_by_orderId(cls, orderId):
        return cls.query.filter_by(_id=orderId).first()

    @classmethod
    def find_by_shopId(cls, shopId):
        return cls.query.filter_by(shop_id=shopId).all()

    @classmethod
    def find_by_userId(cls, userId):
        return cls.query.filter_by(user_id=userId).all()