import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth

def load_auth_config():
    """
    Загружает конфигурацию аутентификации из secrets или файла.
    Для Streamlit Cloud используем st.secrets, для локальной разработки - файл.
    """
    try:
        # Пытаемся загрузить из Streamlit secrets
        config = {
            'credentials': {
                'usernames': {}
            }
        }
        
        if 'auth' in st.secrets:
            auth_config = st.secrets['auth']
            for user in auth_config['usernames']:
                config['credentials']['usernames'][user['username']] = {
                    'name': user['name'],
                    'password': user['password']
                }
            
            config['cookie'] = {
                'expiry_days': 30,
                'key': 'avcs_sim_auth_key',
                'name': 'avcs_sim_auth_cookie'
            }
            config['preauthorized'] = {'emails': []}
            
            return config
        else:
            # Для локальной разработки - читаем из файла
            with open('config.yaml') as file:
                config = yaml.load(file, Loader=SafeLoader)
                return config
    except Exception as e:
        st.error(f"Error loading authentication config: {e}")
        return None

def init_auth():
    """
    Инициализирует аутентификацию и возвращает объект authenticator
    """
    config = load_auth_config()
    if config:
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['preauthorized']
        )
        return authenticator
    return None

def check_authentication():
    """
    Проверяет аутентификацию пользователя.
    Возвращает (name, authentication_status, username) если успешно.
    """
    authenticator = init_auth()
    if authenticator:
        name, authentication_status, username = authenticator.login('Login', 'main')
        return name, authentication_status, username, authenticator
    return None, None, None, None
