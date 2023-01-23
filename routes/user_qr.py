from flask import request, jsonify
import datetime
import base64
import time
import rsa
from databases import extension


# Запись присутствия студента
def check_qr():
    qr_data = request.json["qr_data"]
    lecture_room = "236"

    google_id = qr_data[:qr_data.find("|")]
    encrypted_time = qr_data[qr_data.find("|") + 1:]
    print(f"{google_id}\n{encrypted_time}\n")
    encrypted_time = base64.b64decode(encrypted_time)

    # user = db.user.find({"google_id": google_id})[0]
    user = f''' select * from users where google_id={google_id}'''
    user = extension.execute_read_query(user)[0]
    private_key = user["private_key"]
    private_key = rsa.PrivateKey.load_pkcs1(private_key)

    decrypted_time = rsa.decrypt(encrypted_time, private_key)
    decrypted_time = int(decrypted_time.decode())

    current_time = time.time()

    print(current_time - decrypted_time)
    if (current_time - decrypted_time) < 35:
        check_in_time = datetime.datetime.now()
        in_lesson_list = f''' select * from lesson_list where email = {user['email']} '''
        in_lesson_list = extension.execute_read_query(in_lesson_list)[0]

        if not in_lesson_list:
            add_in_list = f'''' insert into lesson_list (last_name, first_name, email, check_in_float, check_in_time, lecture_room) 
                values ({user['last_name']}, {user['first_name']}, {user['email']}, 
                        {current_time}, {[check_in_time]}, {lecture_room}) '''
            extension.execute_query(add_in_list)
            status = 'Added'
        elif in_lesson_list and ((current_time - in_lesson_list[0]['check_in_float']) > 30):
            update_in_list = f'''' insert into lesson_list (last_name, first_name, email, check_in_float, check_in_time, lecture_room) 
                            values ({user['last_name']}, {user['first_name']}, {user['email']}, 
                                    {current_time}, {[check_in_time]}, {lecture_room}) '''
            extension.execute_query(update_in_list)
            status = f"New check-in time - {check_in_time}"
        else:
            status = f"{user['displayName']} already in list."
    else:
        status = "QR-code is not actual."

    return jsonify({'status': status})