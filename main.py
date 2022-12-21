from flask import Flask, jsonify, request, abort, make_response, render_template
import pymongo
import rsa
import base64
import time
import datetime
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
mongo = pymongo.MongoClient("mongodb+srv://MAERZ:maerz@maerz.snbeycr.mongodb.net/?retryWrites=true&w=majority")
db = mongo.cepu_qr
auth = HTTPBasicAuth()

# with open('scanners.json', 'r', encoding='utf-8') as f:
#     scanners_data = json.load(f)


@app.route('/')
def lists():
    data = list(db.lesson_list.find())
    return render_template('base.html', data=data)


@auth.get_password
def get_password(scan_login):
    if scan_login == "236":  # in scanners_data["scanners"]:
        return "token123"  # scanners_data["scanners"][scan_login]


# Проверка на аутентификацию
@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.route("/user/add", methods=['POST'])
# @auth.login_required()
def home_page():
    if not request.json or not ('displayName' in request.json) or not ('email' in request.json) \
            or not ('google_id' in request.json):
        abort(400)
    user = list(db.user.find({"email": request.json['email']}, {'private_key': 0}))

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
        except Exception as e:
            print(f'Error, user not create', e)

    else:
        user = user[0]
        print(f'Есть в БД:\n{user}')

    return jsonify({'displayName': user.get("displayName"),
                    'email': user.get('email'),
                    'google_id': user.get('google_id'),
                    'public_key': user.get('public_key')})


@app.route('/user/qr', methods=['GET', 'POST'])
# @auth.login_required
def check_user():
    # if not request.json or not request.json["qr_data"]:
    #     abort(400)
    qr_data = request.json["qr_data"]
#     lecture_room = request.json["lecture_room"]

#     qr_data = '116462809506393602287|gEV5OY/WwHBkfXDPUR0c/vATo23x+Sp4ngzEsaQNQcsh5/MhEKZ7AOq7KmeQ+lg+FDFrwj5' \
#               '/07nUl26zxJ8SEypUwfomBxDsC6VTQ1uEJKqhD2yyQ67lPOvGttf14R3UT5KMQpAXm5XojI/WsW9YDWDsSCBKB8cryOH7EEWYm8w= '
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

    print(current_time - decrypted_time)
    if (current_time - decrypted_time) < 24000:
        check_in_time = datetime.datetime.now()
        in_lesson_list = list(db.lesson_list.find({"email": user['email']}))
        if not in_lesson_list:
            db.lesson_list.insert_one(
                {"displayName": user['displayName'], "email": user['email'], "check_in_float": current_time,
                 "check_in_time": [check_in_time], "lecture_room": lecture_room})
            status = 'Added'
        elif in_lesson_list and ((current_time - in_lesson_list[0]['check_in_float']) > 300):
            db.lesson_list.update_one({'_id': in_lesson_list[0]['_id']}, {"$push": {"check_in_time": check_in_time}})
            db.lesson_list.update_one({'_id': in_lesson_list[0]['_id']}, {"$set": {"check_in_float": current_time}})
            status = f"New check-in time - {check_in_time}"
        else:
            status = f"{user['displayName']} already in list."
    else:
        status = "QR-code is not actual."

    return jsonify({'status': status})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(error=str(error)))


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify(error=str(error)))


@app.route("/lesson/list", methods=['GET', 'POST'])
def lesson_list():
    students = list(db.lesson_list.find({}, {"_id": 0, "displayName": 1, "check_in_time": 1}))
    print(students[0]["check_in_time"])
    return jsonify({'list': {"name": students[0]["displayName"], "check-in time": students[0][
        "check_in_time"]}})  # json_encode(students, JSON_UNESCAPED_UNICODE)

    # db.lesson_list.find({check_in_time: {$gte: ISODate("2010-04-29T00:00:00.000Z"),$lt: ISODate(
    # "2023-05-01T00:00:00.000Z")}}, {"_id": 0, "displayName": 1, "check_in_time": 1})


if __name__ == '__main__':
    app.run(debug=True)
