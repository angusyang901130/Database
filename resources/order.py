from flask_restful import Resource, reqparse
from flask import session
from models.order import OrderModel
from utils.logger import create_logger
from sqlalchemy.sql import func

class Order(Resource):
    def __init__(self):
        self.logger = create_logger()

class OrderRegister(Resource):
    def __init__(self):
        self.logger = create_logger()
        
    def post(data):        
        """ if "" in data.values():
            return {'message': 'You do not order anything.'}, 400 """

        try: 
            order = OrderModel("Not Finished", data['orderPrice'], data['shop_id'], data['user_id'], data['shopName'], data['orderDetails'])
            order.save_to_db()
            return {'message': 'Order has been created successfully.'}, 201
        except:
            return {'message': 'Error happened during creating order'}, 500 