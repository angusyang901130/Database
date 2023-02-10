from db import db
import re
from math import sqrt, cos, sin, radians, asin
from decimal import localcontext


class ShopModel(db.Model):
    __tablename__ = 'Shops'
    _id = db.Column('id', db.Integer, primary_key=True)
    shopName = db.Column('shopName', db.String(50), unique=True, nullable=False)
    shopCategory = db.Column('shopCategory', db.String(20, collation='NOCASE'), nullable=False)
    latitude = db.Column('latitude', db.Float(32))
    longitude = db.Column('longitude', db.Float(32))

    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    # users = db.relationship('UserModel', backref='shopkeeper')

    def __init__ (self, shopName, shopCategory, longitude, latitude, user_id):
        self.shopName = shopName
        self.shopCategory = shopCategory
        self.latitude = latitude
        self.longitude = longitude
        self.user_id = user_id
    
    def json(self):
        return {'name': self.shopName, 'items': [item.json() for item in self.items.all()]}
    
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
    
    def get_distance(self, user_lat, user_lng):       
        with localcontext() as ctx:
            ctx.prec = 20
            """ earth_radius = 6378.137
            
            user_lat = user_lat * math.pi / 180
            user_lng = user_lng * math.pi / 180

            shop_lat = self.latitude
            shop_lng = self.longitude
            shop_lat = shop_lat * math.pi / 180
            shop_lng = shop_lng * math.pi / 180
            a = (user_lat) - (shop_lat)
            b = (user_lng) - (shop_lng)
            num1 = math.pow(sin(a/2), 2)
            num2 = cos(user_lat)
            num3 = cos(shop_lat)
            num4 = math.pow(sin(b/2), 2)

            d = num1 + num2 * num3 * num4
            d = 2 * asin(math.sqrt(d))
            d *= earth_radius
            print(d)
            return d """
            earth_radius = 6371
            user_lat = radians(user_lat)
            user_lng = radians(user_lng)
            shop_lat = radians(self.latitude)
            shop_lng = radians(self.longitude)

            dlat = (shop_lat) - (user_lat) 
            dlng = (shop_lng) - (user_lng)

            a = sin(dlat / 2)**2 + cos(user_lat) * cos(shop_lat) * sin(dlng / 2)**2
            b = 2 * asin(sqrt(a))
            d = b * earth_radius
            return d

    def in_dis_range(self, user_lat, user_lng, dis):
        dis_range = [0, 10, 20, float("inf")]
        target = 0
        if dis == "":
            target = 0
        elif dis == "near":
            target = 1
        elif dis == "medium":
            target = 2
        elif dis == "far":
            target = 3
        d = self.get_distance(user_lat, user_lng)
        if target == 0:
            return d, True
        elif d >= dis_range[target-1] and d < dis_range[target]:
            return d, True
        else:
            return d, False
    ##### Find ######
    @classmethod
    def find_by_shopName(cls, shopName):
        return cls.query.filter_by(shopName=shopName).first()

    @classmethod
    def find_by_userId(cls, userId):
        return cls.query.filter_by(user_id=userId).first()

    @classmethod
    def find_by_shopCategory(cls, shopCategory):
        return cls.query.filter_by(shopCategory=shopCategory).all()
    
    @classmethod
    def find_by_shopId(cls, shopId):
        return cls.query.filter_by(_id=shopId).first()

    ##### check #####
    """ @classmethod
    def check_shopName_content(cls, content):
        result = re.findall('[ a-zA-Z]*', content)
        if len(result[0]) == len(content):
            return True
        else:
            return False """

    @classmethod
    def check_shop_latitude(cls, latitude):
        if latitude > 90 or latitude < -90:
            return False
        else:
            return True
    
    @classmethod
    def check_shop_longitude(cls, longitude):
        if longitude > 180 or longitude < -180:
            return False
        else:
            return True

    @classmethod
    def check_is_number(cls, content):
        result = re.findall('[0-9]*', content)
        if len(result[0]) == len(content):
            return True
        else:
            return False
