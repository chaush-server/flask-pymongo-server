from flask import Flask
from routes import home, user_add, user_qr
from security import auth
import locale

app = Flask(__name__, template_folder='templates')
locale.setlocale(locale.LC_ALL, '')

# Главная страница
app.add_url_rule('/', view_func=auth.login_required(home.home))
# Добавления нового пользователя
app.add_url_rule('/user/add', methods=['POST'], view_func=user_add.add)
# Сканирование QR-кода
app.add_url_rule('/user/qr', methods=['POST'], view_func=user_qr.check_qr)

if __name__ == '__main__':
    app.run(debug=True)
