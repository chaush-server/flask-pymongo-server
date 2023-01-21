from flask import Flask, jsonify, request, abort, make_response, render_template
import pymongo
import rsa
import base64
import time
import datetime
from flask_httpauth import HTTPBasicAuth
import locale

locale.setlocale(locale.LC_ALL, '')
app = Flask(__name__, template_folder='templates')
mongo = pymongo.MongoClient("mongodb+srv://MAERZ:maerz@maerz.mippbzs.mongodb.net/?retryWrites=true&w=majority")
db = mongo.cepu_qr
auth = HTTPBasicAuth()


@auth.get_password
def get_password(scan_login: str):
    """Тут задаються возможные кабинеты и пароль к ним"""
    if scan_login in ('236', '239', '238', '233'):
        return "cepu!scanner!secret"
    # При интеграции с окружением использовать следующий код:
    # if scan_login in os.environ.get('CABINETS'):
    #     return os.environ.get('PASS')


@app.route('/log')
@auth.login_required()
def login():
    return jsonify({'status': 1})


@app.route('/', methods=['GET'])
def lists():
    data = list()
    sorting = dict()
    lessons = ['8:00', '9:40', '11:30', '13:10', '14:50', '16:30', '18:10']
    # Проверка на аргументы и передача на страницу
    if request.args.get('date') and request.args.get('time') and request.args.get('lecture_room'):
        date_form = datetime.datetime.strptime(request.args.get('date'), "%Y-%m-%d")
        date_dict = datetime.datetime.strftime(date_form, '%B, %d').replace('0', ' ')
        sorting = {'date_form': request.args.get('date'), 'date': date_dict, 'time': request.args.get('time'),
                   'lecture_room': request.args.get('lecture_room')}
        data = list(db.lesson_list.find().sort("last_name"))
    print(data)
    return render_template('index.html', lessons=lessons, data=data, sorting=sorting)


@app.route("/user/add", methods=['POST'])
def home_page():
    """
    Эта функция испльзуеться в qr учеников для регистрации или авторизации login
    required не нужен
    """
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
                {"last_name": request.json['displayName'].split()[-1],
                 "first_name": request.json['displayName'].split()[0],
                 "email": request.json['email'], "google_id": request.json['google_id'], "public_key": public_key,
                 "private_key": private_key,
                 "displayName": request.json['displayName']})
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
@auth.login_required
def check_user():
    """Функция для записи присутствия ученика"""
    qr_data = request.json["qr_data"]
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
    if (current_time - decrypted_time) < 35:
        check_in_time = datetime.datetime.now()
        in_lesson_list = list(db.lesson_list.find({"email": user['email']}))
        if not in_lesson_list:
            db.lesson_list.insert_one(
                {"last_name": user['last_name'], "first_name": user['first_name'], "email": user['email'],
                 "check_in_float": current_time, "check_in_time": [check_in_time], "lecture_room": lecture_room})
            status = 'Added'
        elif in_lesson_list and ((current_time - in_lesson_list[0]['check_in_float']) > 30):
            db.lesson_list.update_one({'_id': in_lesson_list[0]['_id']}, {"$push": {"check_in_time": check_in_time}})
            db.lesson_list.update_one({'_id': in_lesson_list[0]['_id']}, {"$set": {"check_in_float": current_time}})
            status = f"New check-in time - {check_in_time}"
        else:
            status = f"{user['displayName']} already in list."
    else:
        status = "QR-code is not actual."

    return jsonify({'status': status})


@app.route("/lesson/list", methods=['GET', 'POST'])
def lesson_list():
    """Тестовая функция для вывода всех входов"""
    students = list(db.lesson_list.find({}, {"_id": 0, "displayName": 1, "check_in_time": 1}))
    print(students[0]["check_in_time"])
    return jsonify({'list': {"name": students[0]["displayName"], "check-in time": students[0][
        "check_in_time"]}})


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(error=str(error)))


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify(error=str(error)))


if __name__ == '__main__':
    app.run(debug=True)
