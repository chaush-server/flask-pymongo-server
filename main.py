from flask import Flask, jsonify, request, abort, make_response
import pymongo
import rsa
import base64
import time
import datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
mongo = pymongo.MongoClient(
    "mongodb+srv://MAERZ:maerz@maerz.snbeycr.mongodb.net/?retryWrites=true&w=majority")
db = mongo.cepu_qr
auth = HTTPBasicAuth()


users = {
    "john": generate_password_hash("hello"),
    "susan": generate_password_hash("bye")
}


# @auth.verify_password
# def verify_password(username, password):
#     if username in users and \
#             check_password_hash(users.get(username), password):
#         return username


@auth.get_password
def get_password(username):
    if username == '236':
        return 'token123'


# @auth.error_handler
# def unauthorized():
#     return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.route("/user/add", methods=['POST'])
# @auth.login_required()
def home_page():
    if not request.json or not 'displayName' in request.json or not 'email' in request.json \
            or not 'google_id' in request.json:
        abort(400)

    user = list(db.user.find({"email": request.json['email']}, {'private_key': 0}))
    # user = list(db.user.find({"email": request.json['email']}))

    if not user:
        public_key, private_key = rsa.newkeys(1024)
        public_key = public_key.save_pkcs1().decode('utf-8')
        private_key = private_key.save_pkcs1().decode('utf-8')

        try:
            db.user.insert_one(
                {"displayName": request.json['displayName'], "email": request.json['email'],
                 "google_id": request.json['google_id'], "public_key": public_key, "private_key": private_key})
            print(f'Create user')
            user = list(db.user.find({"email": request.json['email']}, {'private_key': 0}))[0]
        except:
            print(f'Error, user not create')

    else:
        user = user[0]
        print(f'Есть в БД:\n{user}')

    return jsonify({'displayName': user['displayName'],
                    'email': user['email'],
                    'google_id': user['google_id'],
                    'public_key': user['public_key']})


@app.route('/user/qr', methods=['GET', 'POST'])
@auth.login_required
def check_user():
    # if not request.json or not request.json["qr_data"]:
    #     abort(400)
    global status
    # qr_data = request.json["qr_data"]
    # lecture_room = request.json["lecture_room"]

    qr_data = '109914322445815934361|M7Vgj5Jj2AeoxJ3uyxiAg+F/MQ2tP6sEk89+4kPr8mX6bVojlJB9SyDuu94jPrj+/tApkxbyB9R+90V8Ceh' \
              'i150w7uL12uCbAX2b7cX4PYuavLK849ZSNf5WLnmWqw8/3OwG6uqDjzOTHo9ySg00FPhm3bJ2i7Gwr931OLLK27o='
    lecture_room = "236"

    google_id = qr_data[:qr_data.find("|")]
    encrypted_time = qr_data[qr_data.find("|") + 1:]
    print(f"{google_id}\n{encrypted_time}\n")

    encrypted_time = base64.b64decode(encrypted_time)
    user = db.user.find({"google_id": google_id})[0]
    private_key = user["private_key"]
    private_key = rsa.PrivateKey.load_pkcs1(private_key)

    decrypted_time = rsa.decrypt(encrypted_time, private_key)
    decrypted_time = int(decrypted_time.decode())

    current_time = time.time()
    check_in_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    # print(current_time - decrypted_time)

    if (current_time - decrypted_time) < 240:
        in_lesson_list = list(db.lesson_list.find({"email": user['email']}))
        if not in_lesson_list:
            db.lesson_list.insert_one(
                {"displayName": user['displayName'], "email": user['email'],
                 "check_in_time": check_in_time, "lecture_room": lecture_room})
            print(f"Записан:\n{user['displayName']}  {check_in_time[:10]}  {check_in_time[11:]}  {lecture_room}")
        else:
            print(f"{user['displayName']} уже в списке.")
            status = f"{user['displayName']} already in list."
    else:
        print(base64.b64decode("bWlndWVsOnB5dGhvbg==").decode())
        print("QR-код неактуален.")
        status = "QR-code is not actual."

    return jsonify({'Status': status})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'This is not json'}), 404)


if __name__ == '__main__':
    app.run(debug=True)