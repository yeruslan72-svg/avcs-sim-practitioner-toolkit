import streamlit as st
import streamlit_authenticator as stauth

def check_authentication():
    """
    Упрощённая аутентификация для GitHub.
    """
    # Создаём тестового пользователя прямо в коде
    credentials = {
        "usernames": {
            "practitioner001": {
                "email": "test@avcs.com",
                "name": "Test Practitioner",
                "password": "abc123"  # В продакшене нужно хешировать!
            }
        }
    }

    cookie = {
        'expiry_days': 30,
        'key': 'avcs_sim_key',
        'name': 'avcs_sim_auth'
    }

    authenticator = stauth.Authenticate(
        credentials,
        cookie['name'],
        cookie['key'],
        cookie['expiry_days']
    )

    name, authentication_status, username = authenticator.login(fields={'Form name':'Login'}, location='main')

    if authentication_status == False:
        st.error("Username/password is incorrect")

    if authentication_status == None:
        st.warning("Please enter your credentials")

    return name, authentication_status, username, authenticator
