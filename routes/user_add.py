from flask import request, abort, jsonify
import rsa
from databases import extension


# Добавление пользователей в БД
def add():
    if not request.json or not ('email' in request.json):
        abort(400)
    check_user = f''' select * from users where email = "{request.json['email']}" '''
    check_user = extension.execute_read_query(check_user)

    if not check_user:
        # insert_new_user = f'''INSERT INTO users(first_name, last_name, email, google_id, public_key, private_key, displayName)
        # VALUES('фвы', 'фывфыв', 'фыввыф', 'ыфв', 'вфы', 'выф', 'выф')'''
        first_name = request.json['displayName'].split()[0]
        last_name = request.json['displayName'].split()[-1]

        public_key, private_key = rsa.newkeys(1024)
        public_key = public_key.save_pkcs1().decode('utf-8')
        private_key = private_key.save_pkcs1().decode('utf-8')

        insert_new_user = f''' insert into users (last_name, first_name, email, google_id, public_key, private_key, displayName)
                VALUES ('{last_name}', '{first_name}', '{request.json['email']}', '{request.json['google_id']}', 
                '{public_key}', '{private_key}', '{request.json['displayName']}') '''
        extension.execute_query(insert_new_user)
    else:
        check_user = check_user[0]

    return check_user
    # user = list(db.user.find({"email": request.json['email']}, {'private_key': 0}))
    #
    # if not user:
    #     public_key, private_key = rsa.newkeys(1024)
    #     public_key = public_key.save_pkcs1().decode('utf-8')
    #     private_key = private_key.save_pkcs1().decode('utf-8')
    #
    #     try:
    #         db.user.insert_one(
    #             {"last_name": request.json['displayName'].split()[-1],
    #              "first_name": request.json['displayName'].split()[0],
    #              "email": request.json['email'], "google_id": request.json['google_id'], "public_key": public_key,
    #              "private_key": private_key,
    #              "displayName": request.json['displayName']})
    #         print(f'Create user')
    #         user = list(db.user.find({"email": request.json['email']}, {'private_key': 0}))[0]
    #     except Exception as e:
    #         print(f'Error, user not create', e)
    # else:
    #     user = user[0]
    #     print(f'Есть в БД:\n{user}')
    #
    # return jsonify({'displayName': user.get("displayName"),
    #                 'email': user.get('email'),
    #                 'google_id': user.get('google_id'),
    #                 'public_key': user.get('public_key')})

