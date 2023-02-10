from flask_restful import Resource
from flask import make_response, render_template
from models.user import UserModel
from utils.logger import create_logger
import hashlib

# TODO: add AJAX
class User(Resource):
    def __init__(self):
        self.logger = create_logger()
    
    # login (submit the information)
    def post(data):

        # Model.query 是 db.session.query(Model) 的快捷方式
        # one_or_none() -> 查不到結果會回傳 None
        # user = UserModel.find_by_account(data['account'])
        if "" in data.values():
            return {'message': 'Blank is not allowed!!'}, 401

        user = UserModel.query.filter_by(account=data['account']).one_or_none()
        if not user:
            return {'message': 'Wrong account'}, 401
        elif not user.check_password(data['password']):
            return {'message': 'Wrong password'}, 401

        #access_token = create_access_token(identity=json.dumps(user, cls=AlchemyEncoder))

        # return jsonify(access_token=access_token)
        return {'message': 'Login successfully', 'user_account': user.account}, 200

class UserRegister(Resource):
    def __init__(self):
        self.logger = create_logger()

    def post(data):

        if "" in data.values():
            return {'message': 'Blank is not allowed!!'}, 400
        # check the content
        if not UserModel.check_username_content(data["username"]):
            return {'message': 'Username content is wrong!!'}, 400
        if not UserModel.check_phoneNumber_content(data['phoneNumber']):
            return {'message': 'Phone number content is wrong!!'}, 400
        if not UserModel.check_content(data['account']):
            return {'message': 'Account content is wrong!!'}, 400
        if not UserModel.check_content(data['password']):
            return {'message': 'Password content is wrong!!'}, 400
        if data['password'] != data['re-type-password']:
            return {'message': 'Re-type-password is wrong!!'}, 400
        if not UserModel.check_user_longitude(data['longitude']):
            return {'message': 'Longitude is wrong!!'}, 400
        if not UserModel.check_user_latitude(data['latitude']):
            return {'message': 'Latitude is wrong!!'}, 400
        
        # 重複的帳號
        if UserModel.find_by_account(data['account']):
            return {'message': 'Account has already been created, aborting.'}, 400

        hash_password = UserModel.encode(data['password'])

        user = UserModel(data['account'], hash_password, data['username'], data['phoneNumber'], float(data['longitude']), float(data['latitude']))
        try:
            user.save_to_db()
            return {'message': 'User has been created successfully.'}, 201
        except:
            return {'message': 'Error happened during creating user'}, 500 

    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('sign-up.html'),200,headers)

