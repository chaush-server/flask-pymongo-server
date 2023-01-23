from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()


@auth.get_password
def get_password(scan_login: str) -> str:
    """Тут задаються возможные кабинеты и пароль к ним"""
    if scan_login in ('236', '239', '238', '233'):
        return "123"
    # При интеграции с окружением использовать следующий код:
    # if scan_login in os.environ.get('CABINETS'):
    #     return os.environ.get('PASS')
