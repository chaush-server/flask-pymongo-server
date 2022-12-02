from flask import Flask, jsonify, request, abort, make_response
import pymongo
import rsa
import base64
import time
import datetime

app = Flask(__name__)
mongo = pymongo.MongoClient(
    "mongodb+srv://MAERZ:maerz@maerz.snbeycr.mongodb.net/?retryWrites=true&w=majority")
db = mongo.cepu_qr


@app.route("/user/add", methods=['POST'])
def home_page():
    if not request.json or not 'displayName' in request.json or not 'email' in request.json \
            or not 'google_id' in request.json:
        abort(400)

    # user = list(db.user.find({"email": request.json['email']}, {'private_key': 0}))
    user = list(db.user.find({"email": request.json['email']}))

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


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'This is not json'}), 404)


@app.route('/user/qr', methods=['GET', 'POST'])
def check_user():
    # if not request.json or not request.json["qr_data"]:
    #     abort(400)

    # qr_data = request.json["qr_data"]
    # lecture_room = request.json["lecture_room"]
    qr_data = '109914322445815934361|AvUkYNmXJPx/p4w8lS07VdPeDgrnoQzixyDVSAufkFYCkvTH1PeCt5MWv8q7MrafLV7yyMYJqNp2+' \
              'uLWpMmiGPvwdARRXA72dFSTT0OE9WS+KPdEHoSVZfI3P5Pj756drXmhJQRaLNbaQcq2jAKYxKg3NGm45O9HJAuFKKihwKA='
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
    print(current_time - decrypted_time)

    if (current_time - decrypted_time) < 240:
        in_lesson_list = list(db.lesson_list.find({"email": user['email']}))
        if not in_lesson_list:
            db.lesson_list.insert_one(
                {"displayName": user['displayName'], "email": user['email'],
                 "check_in_time": check_in_time, "lecture_room": lecture_room})
            print(f"Записан:\n{user['displayName']}  {check_in_time[:10]}  {check_in_time[11:]}  {lecture_room}")
        else:
            print(f"{user['displayName']} уже в списке.")
    else:
        return jsonify({'Code': "QR-code is not actual."})

    return jsonify({'Code': 'OK.'})


if __name__ == '__main__':
    app.run(debug=True)