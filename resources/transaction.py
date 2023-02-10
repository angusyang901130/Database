from flask_restful import Resource, reqparse
from flask import session
from models.transaction import TransactionModel
from utils.logger import create_logger
from sqlalchemy.sql import func

class Transaction(Resource):
    def __init__(self):
        self.logger = create_logger()

class TransactionRegister(Resource):
    def __init__(self):
        self.logger = create_logger()
    def post(transactionType, moneyChange, transactionTrader, user_id):
        # if "" in data.values():
        #     return {'message': 'Blank in Transaction.'}, 400
        try: 
            transaction = TransactionModel(transactionType, moneyChange, transactionTrader, user_id)
            #print(transaction.transactionTime, transaction.transactionTrader)
            transaction.save_to_db()
            return {'message': 'Transaction has been created successfully.'}, 201
        except:
            return {'message': 'Error happened during creating transaction'}, 500 