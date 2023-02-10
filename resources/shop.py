from flask_restful import Resource
from flask import session
from models.shop import ShopModel
from models.item import ItemModel
from utils.logger import create_logger
from sqlalchemy.sql import func

class Shop(Resource):
    def __init__(self):
        self.logger = create_logger()
    
    def post(data):
        shopName = data['shopName']
        shopCategory = data['shopCategory']
        return {'message': 'In shop "post"'}, 200

class ShopRegister(Resource):
    def __init__(self):
        self.logger = create_logger()
                        
    def post(data):
        
        if "" in data.values():
            return {'message': 'Blank is not allowed !!'}, 400

        if ShopModel.find_by_userId(session['user_id']):
            return {'message': 'Shopkeeper has already created the shop, aborting.'}, 400

        # 重複的帳號
        if ShopModel.find_by_shopName(data['shopName']):
            return {'message': 'ShopName has already been created, aborting.'}, 400

        # check the content
        """ if not ShopModel.check_shopName_content(data['shopName']):
            return {'message': 'ShopName content is wrong!!'}, 400 """

        try:
            lat = float(data['latitude'])
            if not ShopModel.check_shop_latitude(lat):
                return {'message': 'Latitude is wrong!!'}, 400
        except:
            return {'message': 'Latitude is wrong!!'}, 400

        try:
            lng = float(data['longitude'])
            if not ShopModel.check_shop_longitude(lng):
                return {'message': 'Longitude is wrong!!'}, 400
        except:
            return {'message': 'Longitude is wrong!!'}, 400

        try:
            shop = ShopModel(data['shopName'], data['shopCategory'], float(data['longitude']), float(data['latitude']), session['user_id'])
        except:
            return {'message': 'Error happened during creating shop'}, 500 

        try:
            shop.save_to_db()
            return {'message': 'Shop has been created successfully.'}, 201
        except:
            return {'message': 'Error happened during creating shop'}, 500 
class ShopSearch(Resource):
    def __init__(self):
        self.logger = create_logger()
    
    #def post(data, shop_list, dis_list):
    def post(data, user_lat, user_lng):

        shopName = data['shop-name']
        shopCategory = data['shopCategory']
        dis = data['distance']
        meal = data['meal']

        if data['lower-price'] == "":
            lower_price = 0
        else:
            lower_price = int(data['lower-price'])
        
        if data['upper-price'] == "":
            upper_price = float('inf')
        else:
            upper_price = int(data['upper-price'])

        items = ItemModel.query.filter(
            ItemModel.itemPrice >= lower_price,
            ItemModel.itemPrice <= upper_price,
            func.lower(ItemModel.itemName).contains(meal.lower())
        ).all()

        shop_id_list = []
        for item in items:
            if item.shop_id not in shop_id_list:
                shop_id_list.append(item.shop_id)

        shops = ShopModel.query.filter(
            func.lower(ShopModel.shopName).contains(shopName.lower()),
            func.lower(ShopModel.shopCategory).contains(shopCategory.lower()),
            ShopModel._id.in_(shop_id_list)
        ).all()

        shop_list = []
        dist_list = {}
        for shop in shops:
            d, in_range = shop.in_dis_range(user_lat, user_lng, dis)
            if in_range:
                dist_list[shop._id] = d
                shop_list.append(shop)
        
        return shop_list, dist_list

        """ copy_list = shop_list
        copy_dis = dis_list

        if shopName != "":
            for (s, dis) in zip(copy_list, copy_dis):
                if shopName.lower() not in s.shopName.lower():
                    shop_list.remove(s)
                    dis_list.remove(dis)
            copy_list = shop_list
            copy_dis = dis_list

        if shopCategory != "":
            for (s, dis) in zip(copy_list, copy_dis):
                if shopCategory.lower() not in s.shopCategory.lower():
                    shop_list.remove(s)
                    dis_list.remove(dis)
            copy_list = shop_list
            copy_dis = dis_list

        for (s, dis) in zip(copy_list, copy_dis):
            if ItemSearch.post(s._id, lower_price, upper_price, meal) == False:
                shop_list.remove(s)
                dis_list.remove(dis) 

        return shop_list, dis_list"""
