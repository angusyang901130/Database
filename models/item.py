from db import db
import re
from flask import session

#TODO: item information be stored in table, connect to shop
class ItemModel(db.Model):
    __tablename__ = 'Items'
    _id = db.Column('id', db.Integer, primary_key=True)
    itemName = db.Column('itemName', db.String(50), nullable=False)
    itemPrice = db.Column('itemPrice', db.Integer, nullable=False)
    itemRemain = db.Column('itemRemain', db.Integer, nullable=False)
    itemPicture = db.Column('itemPicture', db.LargeBinary(65536), nullable=False)

    shop_id = db.Column(db.Integer, db.ForeignKey('Shops.id'))
    shop = db.relationship('ShopModel', backref='Items')

    def __init__(self, itemName, itemPrice, itemRemain, itemPicture, shop_id):
        self.itemName = itemName
        self.itemPrice = itemPrice
        self.itemRemain = itemRemain
        self.itemPicture = itemPicture
        self.shop_id = shop_id

    
    def json(self):
        return {'name': self.itemName, 'price': self.itemPrice, 'number': self.itemRemain, 'store': self.shop_id}

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return {'message': 'Item is deleted!!'}
        except:
            return {'message': 'Error during deleting item!!'}

    def modify_from_db(self, itemPrice , itemRemain):
        try:
            self.itemPrice = itemPrice
            self.itemRemain = itemRemain
            db.session.commit()
            return {'message': 'Item has been modified!!'}
        except:
            return {'message': 'Error during modifying item!!'}

    # return message? T/F?
    def change_remain_modify_from_db(self , orderNumber):
        try:
            itemRemain = self.itemRemain
            itemRemain -= orderNumber
            if itemRemain >= 0:
                self.itemRemain = itemRemain
                #print(self.itemRemain)
                db.session.commit()
                return {'message': 'Item remain has been modified!!'}
            else:
                return {'message': 'Error during modifying item!!'}
        except:
            return {'message': 'Error during modifying item!!'}
    ##### Find ######
    @classmethod
    def find_by_itemName(cls, itemName):
        return cls.query.filter_by(itemName=itemName, shop_id=session['shop_id']).all()

    @classmethod
    def find_by_itemName_and_shopId(cls, itemName, shop_id):
        return cls.query.filter_by(itemName=itemName, shop_id=shop_id).first()
    
    @classmethod
    def find_by_item_shopId(cls, shopId):
        return cls.query.filter_by(shop_id=shopId).all()

    @classmethod
    def find_by_item_id(cls, itemId):
        return cls.query.filter_by(_id=itemId).first()

    @classmethod
    def find_by_itemPrice(cls, itemPrice_lower, itemPrice_upper):
        if itemPrice_lower == "" and itemPrice_upper == "":
            return cls.query.all()
        elif itemPrice_lower != "" and itemPrice_upper != "":
            return cls.query.filter(
                cls.itemPrice >= itemPrice_lower,
                cls.itemPrice <= itemPrice_upper
            ).all()
        elif itemPrice_lower != "":
            return cls.query.filter(
                cls.itemPrice >= itemPrice_lower
            ).all()
        elif itemPrice_upper != "":
            return cls.query.filter(
                cls.itemPrice <= itemPrice_upper
            ).all()

    ##### check #####
    @classmethod
    def check_itemName_content(cls, content):
        result = re.findall('[a-zA-Z\s]*', content)
        if len(result[0]) == len(content):
            return True
        else:
            return False
    
    @classmethod
    def check_is_number(cls, content):
        try:
            content = str(content)
            result = re.findall('[0-9]*', content)
            if len(result[0]) == len(content):
                return True
            else:
                return False
        except:
            return False

    @classmethod
    def check_itemPrice_value(cls, value):
        if value >= 0:
            return True
        else:
            return False
            
    @classmethod
    def check_itemRemain_value(cls, value):
        if value >= 0:
            return True
        else:
            return False