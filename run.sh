python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg2://user:pass@localhost:5432/cambs_cipher'
python app.py