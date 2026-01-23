import os
import requests

DB_SERVICE = os.environ.get('DB_SERVICE_URL', 'http://127.0.0.1:5600')
API_KEY = os.environ.get('DB_SERVICE_API_KEY') or os.environ.get('DB_API_KEY')

def _headers():
    if API_KEY:
        return {'X-API-KEY': API_KEY}
    return {}

def _url(path):
    return DB_SERVICE.rstrip('/') + path

def list_challenges():
    r = requests.get(_url('/api/challenges'), headers=_headers())
    r.raise_for_status()
    return r.json()

def get_challenge(ch_id):
    r = requests.get(_url(f'/api/challenges/{ch_id}'), headers=_headers())
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def start_attempt(user_id, ch_id):
    r = requests.post(_url(f'/api/challenges/{ch_id}/attempt'), json={'user_id': user_id}, headers=_headers())
    r.raise_for_status()
    return r.json()

def submit_answer(user_id, ch_id, answer):
    r = requests.post(_url(f'/api/challenges/{ch_id}/submit'), json={'user_id': user_id, 'answer': answer}, headers=_headers())
    r.raise_for_status()
    return r.json()

def get_user_by_username(username):
    r = requests.get(_url(f'/api/users/by-username/{username}'), headers=_headers())
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def get_user_by_email(email):
    r = requests.get(_url(f'/api/users/by-email/{email}'), headers=_headers())
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def get_user_by_id(user_id):
    r = requests.get(_url(f'/api/users/{user_id}'), headers=_headers())
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def create_user(data):
    r = requests.post(_url('/api/users'), json=data, headers=_headers())
    r.raise_for_status()
    return r.json()

def update_user(user_id, data):
    r = requests.put(_url(f'/api/users/{user_id}'), json=data, headers=_headers())
    r.raise_for_status()
    return r.json()

def delete_user(user_id):
    r = requests.delete(_url(f'/api/users/{user_id}'), headers=_headers())
    r.raise_for_status()
    return r.json()

def get_leaderboard():
    r = requests.get(_url('/api/leaderboard'), headers=_headers())
    r.raise_for_status()
    return r.json()

def get_user_completed(user_id):
    r = requests.get(_url(f'/api/users/{user_id}/completed'), headers=_headers())
    r.raise_for_status()
    return r.json()

def update_password(user_id, new_password):
    r = requests.put(_url(f'/api/users/{user_id}/password'), json={'password': new_password}, headers=_headers())
    r.raise_for_status()
    return r.json()
