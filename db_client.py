import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
DB_SERVICE = os.getenv('DB_SERVICE_URL', 'https://cambscipher.tail24ded.ts.net')
API_KEY = os.getenv('DB_SERVICE_API_KEY') or os.getenv('DB_API_KEY')

logger = logging.getLogger(__name__)

if not API_KEY:
    raise RuntimeError("DB_SERVICE_API_KEY or DB_API_KEY must be set to talk to the DB service")

def _headers():
    return {'X-API-KEY': API_KEY}

def _url(path):
    return DB_SERVICE.rstrip('/') + path

def list_challenges():
    try:
        r = requests.get(_url('/api/challenges'), headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching challenges list: {e}")
        return []

def get_challenge(ch_id):
    try:
        r = requests.get(_url(f'/api/challenges/{ch_id}'), headers=_headers(), timeout=10)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching challenge {ch_id}: {e}")
        return None

def start_attempt(user_id, ch_id):
    try:
        r = requests.post(_url(f'/api/challenges/{ch_id}/attempt'), json={'user_id': user_id}, headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error starting attempt for user {user_id} on challenge {ch_id}: {e}")
        raise

def submit_answer(user_id, ch_id, answer):
    try:
        r = requests.post(_url(f'/api/challenges/{ch_id}/submit'), json={'user_id': user_id, 'answer': answer}, headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error submitting answer for user {user_id} on challenge {ch_id}: {e}")
        raise

def get_user_by_username(username):
    try:
        r = requests.get(_url(f'/api/users/by-username/{username}'), headers=_headers(), timeout=10)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching user by username {username}: {e}")
        return None

def get_user_by_email(email):
    try:
        r = requests.get(_url(f'/api/users/by-email/{email}'), headers=_headers(), timeout=10)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching user by email {email}: {e}")
        return None

def get_user_by_id(user_id):
    try:
        r = requests.get(_url(f'/api/users/{user_id}'), headers=_headers(), timeout=10)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching user by ID {user_id}: {e}")
        return None

def create_user(data):
    try:
        r = requests.post(_url('/api/users'), json=data, headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating user: {e}")
        raise

def update_user(user_id, data):
    try:
        r = requests.put(_url(f'/api/users/{user_id}'), json=data, headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise

def delete_user(user_id):
    try:
        r = requests.delete(_url(f'/api/users/{user_id}'), headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise

def get_leaderboard():
    try:
        r = requests.get(_url('/api/leaderboard'), headers=_headers())
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching leaderboard: {e}")
        return []

def get_user_completed(user_id):
    try:
        r = requests.get(_url(f'/api/users/{user_id}/completed'), headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching completed challenges for user {user_id}: {e}")
        return []

def update_password(user_id, new_password):
    try:
        r = requests.put(_url(f'/api/users/{user_id}/password'), json={'password': new_password}, headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating password for user {user_id}: {e}")
        raise
