from flask import session
from flask_restful import Resource
from models.item import ItemModel
from utils.logger import create_logger
from base64 import b64encode

class Item(Resource):

    def __init__(self):
        self.logger = create_logger()

    def post(data):

        if ItemModel.find_by_itemName(data['itemName']):
            return {'message': 'Item has been registered'}, 400

        item = ItemModel(data['itemName'], data['itemPrice'], data['itemRemain'], data['itemPicture'])

        try:
            item.save_to_db()
            return {'message': 'Item has been created successfully.'}, 201
        except:
            return {'message': 'Error happened during inserting item'}, 500   
    
class ItemRegister(Resource):
    def __init__(self):
        self.logger = create_logger()

    def post(data, image):
        img = b64encode(image.read())
        
        if "" in data.values() or img == b'':
            return {'message': 'Blank or no picture is not allowed !!'}, 400
        
        if not ItemModel.check_itemName_content(data['itemName']):
            return {'message': 'ItemName content is wrong!!'}, 400
        
        if ItemModel.find_by_itemName(data['itemName']):
            return {'message': 'Item has already been created!!'}, 400
        
        if not ItemModel.check_is_number(data['itemPrice']):
            return {'message': 'ItemPrice value is wrong!!'}, 400

        if not ItemModel.check_is_number(data['itemRemain']):
            return {'message': 'ItemRemain value is wrong!!'}, 400
        
        if not ItemModel.check_itemPrice_value(int(data['itemPrice'])):
            return {'message': 'ItemPrice should be non-negitve !!'}, 400
        
        if not ItemModel.check_itemRemain_value(int(data['itemRemain'])):
            return {'message': 'ItemRemain should be non-negitive!!'}, 400
        
        item = ItemModel(data['itemName'], int(data['itemPrice']), int(data['itemRemain']), img, session['shop_id'])
        
        try:
            item.save_to_db()
            return {'message': 'Item has been created successfully.'}, 201
        except:
            return {'message': 'Error happened during inserting item'}, 500        

class ItemSearch(Resource):
    def __init__(self):
        self.logger = create_logger()
    
    def get_items(shop_list):
        item_dict = {}
        for shop in shop_list:
            items = ItemModel.find_by_item_shopId(shop._id)
            
            # items.sort(key=lambda, )
            item_dict[shop._id] = items
        return item_dict