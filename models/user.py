from db import db
import re
from werkzeug.security import hmac
import hashlib

# TODO: add relation
class UserModel(db.Model):
    __tablename__ = 'Users'
    _id = db.Column('id', db.Integer, primary_key=True)
    account = db.Column('account', db.String(50), unique=True, nullable=False)
    password = db.Column('passward', db.String(64), nullable=False)
    username = db.Column('username', db.String(20), nullable=False)
    phoneNumber = db.Column('phoneNumber', db.String(10), nullable=False)
    longitude = db.Column('longitude', db.Float(32))
    latitude = db.Column('latitude', db.Float(32))
    value = db.Column('value', db.Integer, nullable=False)
    
    shop = db.relationship('ShopModel', backref="user", uselist='False')

    def __init__ (self, account, password, username, phoneNumber, longitude, latitude):
        self.account = account
        self.password = password
        self.username = username
        self.phoneNumber = phoneNumber
        self.latitude = latitude
        self.longitude = longitude
        self.value = 0
        # self.shop_id = shop_id


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
    
    def modify_from_db(self, latitude, longitude):
        try:
            self.latitude = float(latitude)
            self.longitude = float(longitude)
            db.session.commit()
            return {'message': 'User has been modified!!'}
        except:
            return {'message': 'Error during modifying!!'}

    def modify_recharge_from_db(self, add_value):
        try:
            self.value = self.value + add_value
            db.session.commit()
            return {'message': 'Success to recharge'}
        except:
            return {'message': 'Error during modifying!!'}

    def encode(password):
        m = hashlib.md5()
        m.update(password.encode('utf-8'))
        hash_password = m.hexdigest()
        return hash_password

    def check_password(self, password):
        # use "hmac" to encrypt/decrypt
        hash_password = UserModel.encode(password)
        if hash_password == self.password:
            return True
        else:
            return False
        

    # cls: 類（或子類）本身
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(_id=_id).first()

    @classmethod
    def find_by_account(cls, account):
        return cls.query.filter_by(account=account).first()

    @classmethod
    def find_all_user(cls):
        return cls.query.all()

    # 帳密皆為英文+數字
    @classmethod
    def check_content(cls, content):
        result = re.findall('[a-zA-Z0-9]*', content)
        if len(result[0]) == len(content):
            return True
        else:
            return False
    
    # 名字皆為英文
    @classmethod
    def check_username_content(cls, content):
        result = re.findall('[a-zA-Z]*', content)
        if len(result[0]) == len(content):
            return True
        else:
            return False
    
    # 電話號碼長度為10
    @classmethod
    def check_phoneNumber_content(cls, content):
        # content = str(content)
        result = re.findall('[0-9]*', content)
        if len(result[0]) == 10 and len(result[0]) == len(content):
            return True
        else:
            return False
    
    @classmethod
    def check_user_latitude(cls, latitude):
        try:
            lat = float(latitude)
            if lat > 90 or lat < -90:
                return False
            else:
                return True
        except:
            return False
    
    @classmethod
    def check_user_longitude(cls, longitude):
        try:
            lng = float(longitude)
            if lng > 180 or lng <-180:
                return False
            else:
                return True
        except:
            return False