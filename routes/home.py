from flask import render_template, request
import datetime
from databases import extension


def home():
    data = list()
    sorting = dict()
    lessons = ['8:00', '9:40', '11:30', '13:10', '14:50', '16:30', '18:10']
    if request.args.get('date') and request.args.get('time') and request.args.get('lecture_room'):
        date_form = datetime.datetime.strptime(request.args.get('date'), "%Y-%m-%d")
        date_dict = datetime.datetime.strftime(date_form, '%B, %d').replace('0', ' ')
        sorting = {'date_form': request.args.get('date'),
                   'date': date_dict,
                   'time': request.args.get('time'),
                   'lecture_room': request.args.get('lecture_room')}
        data_users = 'Select * from users'
        data = extension.execute_read_query(data_users)
    return render_template('index.html', lessons=lessons, data=data, sorting=sorting)
    # data = list()
    # sorting = dict()
    # lessons = ['8:00', '9:40', '11:30', '13:10', '14:50', '16:30', '18:10']
    # # Проверка на аргументы и передача на страницу
    # if request.args.get('date') and request.args.get('time') and request.args.get('lecture_room'):
    #     date_form = datetime.datetime.strptime(request.args.get('date'), "%Y-%m-%d")
    #     date_dict = datetime.datetime.strftime(date_form, '%B, %d').replace('0', ' ')
    #     sorting = {'date_form': request.args.get('date'), 'date': date_dict, 'time': request.args.get('time'),
    #                'lecture_room': request.args.get('lecture_room')}
    #     data = list(db.lesson_list.find().sort("last_name"))
    # print(data)
    # return render_template('index.html', lessons=lessons, data=data, sorting=sorting)
