from faulthandler import cancel_dump_traceback_later
from flask import Flask, render_template, request, url_for, redirect, flash, session, jsonify
from flask_sqlalchemy import Pagination
from requests import delete
from db import init_db
from models.user import UserModel
from models.item import ItemModel
from models.shop import ShopModel
from models.order import OrderModel
from models.transaction import TransactionModel
from resources.item import ItemRegister, ItemSearch
from resources.shop import Shop, ShopRegister, ShopSearch
from resources.transaction import TransactionRegister
from resources.user import UserRegister, User
from resources.order import OrderRegister
from flask_restful import Api
import os
from datetime import timedelta

app = Flask(__name__)

# setup db
# app.config['MYSQL_HOST'] = 'db'          # 登入ip
# app.config['MYSQL_USER'] = 'root'               # 登入帳號
# app.config['MYSQL_PASSWORD'] = 'rootroot'           # 登入密碼
# app.config['MYSQL_DB'] = 'db'                   # 登入資料庫名稱
app.config['MYSQL_PORT'] = '5000'             # Port號（預設就是3306)
app.config["SECRET_KEY"] = "DB"

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL','sqlite:///' + os.path.join(app.root_path, 'DB_HW.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config['BABEL_DEFAULT_LOCALE'] = 'en'
# app.config['BABEL_DEFAULT_TIMEZONE']='UTC'

api = Api(app)

shopkeeper_item_list = None
shop_list = None
dist = None
item_dict = None
dist_list = None
user_order_list = None
shopkeeper_order_list = None
test_order = None
cur_order_shop_id = None
order_items = None
transaction_list = None

@app.before_first_request
def create_table():
    init_db(app)

""" @app.before_request
def make_session_permanent():
    session.permanent = False """
    
######### start up #########
def start_session():
    session['user_id'] = None
    session['shop_id'] = None
    global shopkeeper_item_list, shop_list, dist_list, item_dict, user_order_list, shopkeeper_order_list, order_items, transaction_list
    shopkeeper_item_list = None
    shop_list = None
    dist_list = None
    item_dict = None
    user_order_list = None
    shopkeeper_order_list = None
    order_items = None
    transaction_list = None
############################

############  home  ############ 
@app.route("/", methods=["GET", "POST"])
def login():   # form: get data from input
    if 'user_id' not in session.keys():
        start_session()
        
    if request.method == 'GET':
        if session['user_id'] is not None:
            session.permanent = False
            app.permanent_session_lifetime = timedelta(minutes=15)
            return redirect(url_for('nav_home'))
        else:
            return render_template("index.html")
    
    elif request.method == 'POST': 
        data = request.form
        response, status = User.post(data)
        flash(response['message'])

        if status == 401:  
            return redirect(url_for('login'))
            
        elif status == 200:
            session.permanent = False
            app.permanent_session_lifetime = timedelta(minutes=15)
            account = response['user_account']
            session['user_id'] = UserModel.find_by_account(account=account)._id

            return redirect(url_for("nav_home"))

################################ 

############ signup ############ 
@app.route("/sign-up", methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template("sign-up.html")
    
    elif request.method == 'POST':
        data = request.form
        response, status = UserRegister.post(data)
        flash(response['message'])

        if status == 400:
            return redirect(url_for('signup'))
        elif status == 201:
            return redirect(url_for("login"))
################################

############  nav_home ############ 
@app.route("/nav", methods=['POST', 'GET'])
def nav_home():
    if 'user_id' not in session or session['user_id'] is None:
        flash("not login yet")
        return redirect(url_for('login'))
    else:
        if request.method == 'GET':
            user = UserModel.find_by_id(session['user_id'])
            shop = ShopModel.find_by_userId(session['user_id'])
            
            if shop is not None:
                role = 'manager'
                session['shop_id'] = shop._id
                global shopkeeper_item_list, shopkeeper_order_list
                shopkeeper_item_list = ItemModel.find_by_item_shopId(shop._id)
                shopkeeper_order_list = OrderModel.find_by_shopId(shop._id)
            else:
                role = 'user'
                
            global user_order_list, transaction_list
            user_order_list = OrderModel.find_by_userId(user._id)
            transaction_list = TransactionModel.find_by_userId(user._id)

            global shop_list, dist, item_dict
            if shop_list is not None:
                item_dict = ItemSearch.get_items(shop_list)

            paginate = None
            if shop_list is not None:
                limit = len(shop_list) # 5 + 1
                page = request.args.get('page', 1, type=int)
                if page > limit or page < 1:
                    page = 1
                start = (page - 1) * 5
                end = page * 5 if len(shop_list) > page * 5 else len(shop_list)
                paginate = Pagination(shop_list, page, 5, len(shop_list), shop_list[start : end])
                shop_list_inPage = shop_list[start : end]
            else:
                shop_list_inPage = shop_list
            
            #session.permanent = False
            return render_template("nav.html", current_user=user, role=role, shopkeeper_item_list=shopkeeper_item_list, shop_list=shop_list_inPage, dist_list=dist_list, item_dict=item_dict, paginate = paginate, shopkeeper = shop, user_order_list = user_order_list, shopkeeper_order_list = shopkeeper_order_list, transaction_list = transaction_list)
            # return render_template("nav.html", current_user=user, role=role)

        elif request.method == 'POST':
            print("no post yet")

###################################

############ shop search ############
@app.route("/shop_search", methods=['POST', 'GET'])
def shop_search():
    # data = request.form
    # response, status = ShopSearch.post(data)

    global shop_list, dist_list, item_dict
    if request.method == 'GET':
        return redirect(url_for('nav_home'))

    elif request.method == 'POST':
        user = UserModel.find_by_id(session['user_id'])

        data = request.form
        all_blank = True
        for key in data:
            if data[key] != "":
                all_blank = False
                break
        
        if all_blank:
            flash('Must not all blank!')
            return redirect(url_for('nav_home'))
        if not (ItemModel.check_is_number(data['lower-price']) and ItemModel.check_is_number(data['upper-price'])):
            flash('Price should be non-negative integer!')
            return redirect(url_for('nav_home'))
        if data['lower-price'] != "" and data['upper-price'] != "":
            if int(data['lower-price']) > int(data['upper-price']):
                flash('Upper-price should be bigger than Lower-price!')
                return redirect(url_for('nav_home'))

        # return {"message": str(user)}
        lat = user.latitude
        lng = user.longitude
        
        shop_list, dist_list = ShopSearch.post(data, lat, lng)
        item_dict = ItemSearch.get_items(shop_list)

        return redirect(url_for('nav_home'))


####################################

############ shop register ############
@app.route("/shop_register", methods=['POST', 'GET'])
def nav_shop():
    if request.method == 'GET':
        return redirect(url_for('nav_home'))

    elif request.method == 'POST':
        data = request.form
        response, status = ShopRegister.post(data)
        flash(response['message'])
        return redirect(url_for('nav_home'))
        
#######################################

############ item register ############
@app.route("/item_register", methods=['POST', 'GET'])
def nav_item():
    if request.method == 'GET':
        return redirect(url_for('nav_home'))
    elif request.method == 'POST':
        shop = ShopModel.find_by_userId(session['user_id'])
        if shop is None:
            session['shop_id'] = None
            flash("No access right, please register your shop first.")
        else:
            session['shop_id'] = shop._id
            data = request.form
            image = request.files['itemPicture']
            response, status = ItemRegister.post(data, image)
            flash(response['message'])
        return redirect(url_for('nav_home'))
#########################################

############## item modify ##############
@app.route("/item_modify", methods=['POST', 'GET'])
def item_modify():
    if request.method == 'GET':
        return redirect(url_for('nav_home'))
    elif request.method == 'POST':
        data = request.form

        if "" in data.values():
            flash('Blank is not allowed!!')
            return redirect(url_for('nav_home'))

        elif not ItemModel.check_is_number(data['itemPrice']):
            flash('ItemPrice value is wrong!!')

        elif not ItemModel.check_is_number(data['itemRemain']):
            flash('ItemRemain value is wrong!!')
        
        elif not ItemModel.check_itemPrice_value(int(data['itemPrice'])):
            flash('ItemPrice value is wrong!!')
        
        elif not ItemModel.check_itemRemain_value(int(data['itemRemain'])):
            flash('ItemRemain value is wrong!!')

        else:
            item = ItemModel.find_by_item_id(data['item_id'])
            message = item.modify_from_db(data['itemPrice'], data['itemRemain'])
            flash(message['message'])
        # else:
        #     flash('The value should be integer!!')
        return redirect(url_for('nav_home'))
######################################

############# location modify ###########
@app.route("/location_modify", methods=['POST', 'GET'])
def location_modify():
    if request.method == 'GET':
        return redirect(url_for('nav_home'))
    elif request.method == 'POST':
        data = request.form

        if "" in data.values():
            flash('Blank is not allowed!!')
            return redirect(url_for('nav_home'))

        user = UserModel.find_by_id(session['user_id'])
        try:
            new_lat = float(data['latitude'])
            new_lon = float(data['longitude'])
        except:
            flash('The value would not accept')
            return redirect(url_for('nav_home'))

        if not (UserModel.check_user_latitude(new_lat) and UserModel.check_user_longitude(new_lon)):
            flash('The value would not accept')
            return redirect(url_for('nav_home'))
            
        message = user.modify_from_db(data['latitude'], data['longitude'])
        flash(message['message'])
        return redirect(url_for('nav_home'))
#########################################

############# recharge modify ###########
@app.route("/recharge", methods=['POST', 'GET'])
def recharge():
    if request.method == 'GET':
        return redirect(url_for('nav_home'))
    elif request.method == 'POST':
        data = request.form

        if "" in data.values():
            flash('Blank is not allowed!!')
            return redirect(url_for('nav_home'))

        user = UserModel.find_by_id(session['user_id'])
        try:
            add_money = int(data['recharge_value'])
            if add_money != abs(add_money):
                flash('The value would not accept')
                return redirect(url_for('nav_home'))
        except:
            flash('The value would not accept')
            return redirect(url_for('nav_home'))
        message = user.modify_recharge_from_db(add_money)
        response, status = TransactionRegister.post("Recharge", "+" + str(add_money), user.account, user._id)
        flash(message['message'])
        if status != 201:
            message = user.modify_recharge_from_db(-add_money)
            flash('Error, please try again')

        return redirect(url_for('nav_home'))
#########################################

#############  delete item  #############
@app.route("/item_delete", methods=['POST', 'GET'])
def item_delete():
    if request.method == 'GET':
        return redirect(url_for('nav_home'))
    elif request.method == 'POST':
        data = request.form

        item = ItemModel.find_by_item_id(data['item_id'])
        message = item.delete_from_db()
        flash(message['message'])
        return redirect(url_for('nav_home'))
#########################################

############ sorting_shop ############
@app.route("/sorting", methods=['POST'])
def sorting_shop():
    global shop_list, dist_list
    if shop_list is not None:
        data = request.form
        if data != "":
            sort_type = data['sort_type']
            rev = data['rev']
        else:
            sort_type = "Shop name"
            rev = "increase"
        if rev == "decrease":
            rev = True
        elif rev == "increase":
            rev = False
        if (sort_type == "Shop name"):
            shop_list.sort(key=lambda x: x.shopName.lower(), reverse = rev)
        elif (sort_type == "Shop category"):
            shop_list.sort(key=lambda x: x.shopCategory.lower(), reverse = rev)
        else:
            dist_list = dict(sorted(dist_list.items(), key=lambda x: x[1], reverse = rev))
            new_shop_list = []
            for key in dist_list:
                for s in shop_list:
                    if s._id == key:
                        new_shop_list.append(s)
                        shop_list.remove(s)
                        break
            shop_list = new_shop_list
    return redirect(url_for('nav_home'))


############ check account ############
@app.route('/account_registered', methods=['POST','GET'])
def account_registered():
    if request.method == 'POST':
        account = request.json
        if account == "":
            response = jsonify('<span></span>')
            response.status_code = 200
            return response
        elif not UserModel.check_content(account):
            response = jsonify('<span style=\'color:red;\'>Account format error</span>')
            response.status_code = 200
            return response
        elif UserModel.find_by_account(account=account) is None:
            response = jsonify('<span style=\'color:green;\'>Account available</span>')
            response.status_code = 200
            return response
        else:
            response = jsonify('<span style=\'color:red;\'>Account has been registered</span>')
            response.status_code = 200
            return response
    elif request.method == 'GET':
        return redirect(url_for('signup')) 
#######################################

############ check account ############
@app.route('/shopname_registered', methods=['POST', 'GET'])
def shopname_registered():
    if request.method == 'POST':
        shopName = request.json
        
        if shopName == "":
            response = jsonify('<span></span>')
            response.status_code = 200
            return response
        elif ShopModel.find_by_shopName(shopName=shopName) is None:
            response = jsonify('<span style=\'color:green;\'>Shop name available</span>')
            response.status_code = 200
            return response
        else:
            response = jsonify('<span style=\'color:red;\'>Shop name has been registered</span>')
            response.status_code = 200
            return response
    elif request.method == 'GET':
        return redirect(url_for('nav_home')) 
#######################################

############### menu order ################
@app.route("/show_order", methods=['POST', 'GET'])
def show_order():
    if request.method == 'POST':
        tmp_order = request.json
        #print(tmp_order)
        shop_id = tmp_order['shop_id']
        item_order = tmp_order['item_order']
        delivery = tmp_order['deliver']           

        #items = ItemModel.find_by_item_shopId(shop_id)
        global order_items
        order_items = []

        response = ""
        total_price = 0
        for key, value in item_order.items():
            if int(value) > 0:
                
                item = ItemModel.find_by_item_id(int(key))
                #print(item)
                if item is None or item.itemRemain < int(value):
                    return jsonify("Some items are no longer available or no enough remaining")
        
                response += \
                '<tr id="item-detail-' + str(item._id) + '">'\
                    '<td><img src="data:image/jpeg;base64, ' + item.itemPicture.decode('utf-8') + '" width="50" height="50"> </td>' +\
                    '<td>' + item.itemName + '</td>' +\
                    '<td>' + str(item.itemPrice) + '</td>' +\
                    '<td>' + value + '</td>' +\
                '</tr>'

                total_price += int(value) * item.itemPrice
                tup = (item, int(value), item.itemPrice)
                order_items.append(tup)
        
        if response == "":
            #flash("You didn't order anything !!")
            return jsonify("You didn't order anything !!")

        #print(ordered)
        response += "   " + str(total_price)

        if delivery == "Delivery":
            shop = ShopModel.find_by_shopId(int(shop_id))
            user = UserModel.find_by_id(session['user_id'])

            dist = shop.get_distance(user.latitude, user.longitude)
            deliver_price = round(dist * 10)
            if deliver_price < 10:
                deliver_price = 10

        elif delivery == "Pick-up":
            deliver_price = 0
        
        response += "   " + str(deliver_price)
        global cur_order_shop_id
        cur_order_shop_id = int(shop_id)

        response = jsonify(response)
        response.status = 200
        return response
    elif request.method == 'GET':
        return redirect(url_for('nav_home'))
###########################################

##############  add order ###############
@app.route("/add_order", methods=['POST'])
def order():
    if request.method == 'POST':
        order_detail = request.json
        data = {}
        global cur_order_shop_id
        shop = ShopModel.find_by_shopId(cur_order_shop_id)
        #print(cur_order_shop_id)
        
        if shop == None:
            res = jsonify("This shop is not exist.")
            return res

        data['shopName'] = shop.shopName
        data['orderDetails'] = order_detail['order_item'] + "   " + order_detail['subtotal'] + "   " + order_detail['deliver_fee']
        data['shop_id'] = cur_order_shop_id
        data['user_id'] = session['user_id']

        total = order_detail['total']
        money_sign_index = total.index('$')
        orderPrice = total[money_sign_index+1:]
        data['orderPrice'] = int(orderPrice)

        current_user = UserModel.find_by_id(session['user_id'])
        if current_user.value < data['orderPrice']:
            res = jsonify("Insufficient balance.")
            return res

        global order_items
        for item in order_items:
            check_item = ItemModel.find_by_item_id(item[0]._id)
            if (check_item == None or check_item.itemRemain < item[1] or check_item.itemPrice != item[2]):
                res = jsonify("Error, please try again.")
                return res
        
        for item in order_items:
            #print(": ", item[0])
            #print("quantity: ", item[1])
            it = ItemModel.find_by_item_id(item[0]._id)
            #print(it)
            res = it.change_remain_modify_from_db(item[1])
            #print(res)
            #print(item[0].itemRemain)
            #print(item[0])
            #print(item[0].itemRemain)

        
        #print(item_dict[cur_order_shop_id])
        #for item in item_dict[cur_order_shop_id]:
            #print(item._id, ": ", item.itemRemain)
        # This order is ok
        response, status = OrderRegister.post(data)
        flash(response['message'])

        shopkeeper = UserModel.find_by_id(shop.user_id)
        # print(shopkeeper.userName, shopkeeper._id)


        # transaction
        response1, status1 = TransactionRegister.post("Payment", "-" + str(orderPrice), data['shopName'], session['user_id'])
        response2, status2 = TransactionRegister.post("Receive", "+" + str(orderPrice), data['shopName'], shopkeeper._id)

        # payment & receive
        current_user.modify_recharge_from_db(-int(orderPrice))
        shopkeeper.modify_recharge_from_db(int(orderPrice))


        response = jsonify('http://127.0.0.1:5000/nav')
        return response
    else:
        return jsonify('http://127.0.0.1:5000/nav')
################################################

################# order detail #################
@app.route("/order_detail", methods=['POST', 'GET'])
def myOrder():
    if request.method == 'POST':
        order_id = request.json
        order = OrderModel.find_by_orderId(int(order_id))
        order_detail = order.orderDetails + "   " + "Total: $" + str(order.orderPrice)
        response = jsonify(order_detail)
        response.status = 200
        
        return response
    
    elif request.method == 'GET':
        return redirect(url_for('nav_home'))
#################################################

################ user cancel multi order ################## 
@app.route("/userOrder_select_cancel", methods=['POST'])
def userOrder_select_cancel():
    if request.method == 'POST':
        data = request.form
        data = dict(data)
        #print(dict(data))

        # multi cancel
        key_list = list(data.keys())
        #print(key_list)
        if "multi_cancel" in key_list:
            cancel_list = []
            error_count = 0
            for k, v in data.items():
                if 'cbox-user-' in k:
                    cancel_list.append(v)
            
            if len(cancel_list) == 0:
                flash("You didn't select any order!")
                return redirect(url_for('nav_home'))
            else:
                for i in cancel_list:
                    cancel_order = OrderModel.find_by_orderId(i)
                    if cancel_order == None or cancel_order.orderState != "Not Finished":
                        error_count += 1
                    else:
                        cancel_order.modify_from_db("Cancel")
                        shop = ShopModel.find_by_shopId(cancel_order.shop_id)
                        cancel_shopkeeper = UserModel.find_by_id(shop.user_id)
                        current_user = UserModel.find_by_id(session['user_id'])
                        # transaction
                        response1, status1 = TransactionRegister.post("Receive", "+" + str(cancel_order.orderPrice), cancel_order.shopName, current_user._id)
                        response2, status2 = TransactionRegister.post("Payment", "-" + str(cancel_order.orderPrice), cancel_order.shopName, cancel_shopkeeper._id)
                        
                        # receive & payment
                        current_user.modify_recharge_from_db(int(cancel_order.orderPrice))
                        cancel_shopkeeper.modify_recharge_from_db(int(-cancel_order.orderPrice))

                        # itemRemain return
                        order_detail = cancel_order.orderDetails
                        order_detail = order_detail.split("   ")[0]
                        order_detail = order_detail.replace("</tr>", ",").replace("<td>", ",").replace("</td>", ",")
                        order_detail = order_detail.split(",")
                        for i in range(len(order_detail)):
                            if i % 10 == 2 or i % 10 == 1:
                                order_detail[i] = ""
                            #print(len(order_detail[i]))
                        for i in range(len(order_detail)-1, -1, -1):
                            if len(order_detail[i]) == 0:
                                order_detail.pop(i)

                        #print(order_detail)

                        item_id = -1
                        for i in range(len(order_detail)):
                            if i % 4 == 0:
                                item_id = int(order_detail[i].split("-")[-1].split('">')[0])
                            elif i % 4 == 3:
                                modify_quantity = int(order_detail[i])
                                item = ItemModel.find_by_item_id(item_id)
                                item.change_remain_modify_from_db(-modify_quantity)

            if error_count == 1:
                flash("There is " + str(error_count) + " fail in cancel order.")
            elif error_count > 1:
                flash("There are " + str(error_count) + " fails in cancel order.")
            else:
                flash("Success to cancel orders")
            return redirect(url_for('nav_home'))
        else:
            target = -1
            for k, v in data.items():
                if v == "Cancel":
                    target = k
                    break
            if target == -1:
                flash("Error, please try again!")
                return redirect(url_for('nav_home'))
            cancel_order = OrderModel.find_by_orderId(int(target))
            if cancel_order == None or cancel_order.orderState != "Not Finished":
                flash("Error in cancel this order, please try again.")
            else:
                cancel_order.modify_from_db("Cancel")
                shop = ShopModel.find_by_shopId(cancel_order.shop_id)
                cancel_shopkeeper = UserModel.find_by_id(shop._id)
                current_user = UserModel.find_by_id(session['user_id'])
                #print(current_user.value)
                # transaction
                response1, status1 = TransactionRegister.post("Receive", "+" + str(cancel_order.orderPrice), cancel_order.shopName, current_user._id)
                response2, status2 = TransactionRegister.post("Payment", "-" + str(cancel_order.orderPrice), cancel_order.shopName, cancel_shopkeeper._id)
                        
                # receive & payment
                current_user.modify_recharge_from_db(int(cancel_order.orderPrice))
                #print("user: ",current_user.value)
                cancel_shopkeeper.modify_recharge_from_db(-int(cancel_order.orderPrice))
                #print("shopkeeper: ", cancel_shopkeeper.value)

                # itemRemain return
                order_detail = cancel_order.orderDetails
                order_detail = order_detail.split("   ")[0]
                order_detail = order_detail.replace("</tr>", ",").replace("<td>", ",").replace("</td>", ",")
                order_detail = order_detail.split(",")
                for i in range(len(order_detail)):
                    if i % 10 == 2 or i % 10 == 1:
                        order_detail[i] = ""
                    #print(len(order_detail[i]))
                for i in range(len(order_detail)-1, -1, -1):
                    if len(order_detail[i]) == 0:
                        order_detail.pop(i)

                #print(order_detail)

                item_id = -1
                for i in range(len(order_detail)):
                    if i % 4 == 0:
                        item_id = int(order_detail[i].split("-")[-1].split('">')[0])
                    elif i % 4 == 3:
                        modify_quantity = int(order_detail[i])
                        item = ItemModel.find_by_item_id(item_id)
                        item.change_remain_modify_from_db(-modify_quantity)
                
                flash("Success to cancel orders")
            return redirect(url_for('nav_home'))
#################################################

################ shop cancel/done multi order ################## 
@app.route("/shopOrder_update", methods=['POST'])
def shopOrder_update():
    if request.method == 'POST':
        data = request.form
        data = dict(data)
        #print(dict(data))

        key_list = list(data.keys())

        # 1. multi_finish
        if "multi_finish" in key_list:
            finish_list = []
            error_count = 0
            for k, v in data.items():
                if 'cbox-shop' in k:
                    finish_list.append(v)

            if len(finish_list) == 0:
                flash("You didn't select any order!")
                return redirect(url_for('nav_home'))
            else:
                for i in finish_list:
                    finish_order = OrderModel.find_by_orderId(i)
                    if finish_order == None or finish_order.orderState != "Not Finished":
                        error_count += 1
                    else:
                        finish_order.modify_from_db("Finished")

            if error_count == 1:
                flash("There is " + str(error_count) + " fail in cancel order.")
            elif error_count > 1:
                flash("There are " + str(error_count) + " fails in cancel order.")
            else:
                flash("Success to finish orders")
            return redirect(url_for('nav_home'))

        # 2. multi_cancel
        elif "multi_cancel" in key_list:
            cancel_list = []
            error_count = 0
            for k, v in data.items():
                if 'cbox-shop' in k:
                    cancel_list.append(v)

            if len(cancel_list) == 0:
                flash("You didn't select any order!")
                return redirect(url_for('nav_home'))
            else:
                for i in cancel_list:
                    cancel_order = OrderModel.find_by_orderId(i)
                    if cancel_order == None or cancel_order.orderState != "Not Finished":
                        error_count += 1
                    else:
                        cancel_order.modify_from_db("Cancel")

                        shop = ShopModel.find_by_shopId(cancel_order.shop_id)
                        cancel_shopkeeper = UserModel.find_by_id(shop.user_id)
                        current_user = UserModel.find_by_id(cancel_order.user_id)
                        # transaction
                        response1, status1 = TransactionRegister.post("Receive", "+" + str(cancel_order.orderPrice), cancel_order.shopName, current_user._id)
                        response2, status2 = TransactionRegister.post("Payment", "-" + str(cancel_order.orderPrice), cancel_order.shopName, cancel_shopkeeper._id)
                        
                        # receive & payment
                        current_user.modify_recharge_from_db(int(cancel_order.orderPrice))
                        cancel_shopkeeper.modify_recharge_from_db(-int(cancel_order.orderPrice))

                        # itemRemain return
                        order_detail = cancel_order.orderDetails
                        order_detail = order_detail.split("   ")[0]
                        order_detail = order_detail.replace("</tr>", ",").replace("<td>", ",").replace("</td>", ",")
                        order_detail = order_detail.split(",")
                        for i in range(len(order_detail)):
                            if i % 10 == 2 or i % 10 == 1:
                                order_detail[i] = ""
                            #print(len(order_detail[i]))
                        for i in range(len(order_detail)-1, -1, -1):
                            if len(order_detail[i]) == 0:
                                order_detail.pop(i)

                        #print(order_detail)

                        item_id = -1
                        for i in range(len(order_detail)):
                            if i % 4 == 0:
                                item_id = int(order_detail[i].split("-")[-1].split('">')[0])
                            elif i % 4 == 3:
                                modify_quantity = int(order_detail[i])
                                item = ItemModel.find_by_item_id(item_id)
                                item.change_remain_modify_from_db(-modify_quantity)

                if error_count == 1:
                    flash("There is " + str(error_count) + " fail in cancel order.")
                elif error_count > 1:
                    flash("There are " + str(error_count) + " fails in cancel order.")
                else:
                    flash("Success to cancel orders")
                return redirect(url_for('nav_home'))

        # 3. single finish/cancel
        else:
            target = -1
            action = ""
            for k, v in data.items():
                if v == "Cancel":
                    target = k
                    action = "Cancel"
                    break
                elif v == "Done":
                    target = k
                    action = "Finished"
                    break
            if target == -1:
                flash("Error, please try again!")
                return redirect(url_for('nav_home'))
            
            order = OrderModel.find_by_orderId(int(target))
            if order == None or order.orderState != "Not Finished":
                flash("Error in cancel this order, please try again.")
            else:
                order.modify_from_db(action)
                if action == "Cancel":
                    shop = ShopModel.find_by_shopId(order.shop_id)
                    #print(shop.shopName)
                    shopkeeper = UserModel.find_by_id(shop.user_id)
                    current_user = UserModel.find_by_id(order.user_id)

                    # transaction
                    response1, status1 = TransactionRegister.post("Receive", "+" + str(order.orderPrice), order.shopName, current_user._id)
                    response2, status2 = TransactionRegister.post("Payment", "-" + str(order.orderPrice), order.shopName, shopkeeper._id)
                    #print(response1, response2)
                    # receive & payment
                    current_user.modify_recharge_from_db(int(order.orderPrice))
                    #print(current_user.value, res1)
                    shopkeeper.modify_recharge_from_db(-int(order.orderPrice))

                    # itemRemain return
                    order_detail = order.orderDetails
                    order_detail = order_detail.split("   ")[0]
                    order_detail = order_detail.replace("</tr>", ",").replace("<td>", ",").replace("</td>", ",")
                    order_detail = order_detail.split(",")
                    for i in range(len(order_detail)):
                        if i % 10 == 2 or i % 10 == 1:
                            order_detail[i] = ""
                        #print(len(order_detail[i]))
                    for i in range(len(order_detail)-1, -1, -1):
                        if len(order_detail[i]) == 0:
                            order_detail.pop(i)

                    #print(order_detail)

                    item_id = -1
                    for i in range(len(order_detail)):
                        if i % 4 == 0:
                            item_id = int(order_detail[i].split("-")[-1].split('">')[0])
                        elif i % 4 == 3:
                            modify_quantity = int(order_detail[i])
                            item = ItemModel.find_by_item_id(item_id)
                            item.change_remain_modify_from_db(-modify_quantity)
                    #print(shopkeeper.value, res2)
                    flash("Success to cancel orders")

            return redirect(url_for('nav_home'))
    return redirect(url_for('nav_home'))
        # multi cancel
############################################################


##############  logout  ###############
@app.route("/logout", methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))
#######################################

########## run #############
if __name__ == "__main__":
    app.run(debug=True)
    # app.run()