"""
Script to seed the database with initial challenges.
Run this after starting the app once to create the database.
"""
from app import app, db, Challenges
from datetime import datetime

# Sample challenges - customize these as needed
# release_time and closing_time can be None (always open) or datetime objects
challenges_data = [
    {
        "id": 1,
        "title": "Introduction",
        "published": True,
        "ciphertext": "KHOOR ZRUOG",
        "plaintext": "HELLO WORLD",
        "tips": "This is a Caesar cipher with a shift of 3. Each letter is shifted forward by 3 positions in the alphabet.",
        "points_reward": 5,
        "release_time": None,  # Always available
        "closing_time": None   # Never closes
    },
    {
        "id": 2,
        "title": "Challenge 1 (Practice)",
        "published": True,
        "ciphertext": "WKH TXLFN EURZQ IRA MXPSV RYHU WKH ODCB GRJ",
        "plaintext": "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
        "tips": "Another Caesar cipher. Try different shift values!",
        "points_reward": 10,
        "release_time": datetime(2025, 12, 28, 21, 0),
        "closing_time": datetime(2025, 12, 28, 21, 40)
    },
    {
        "id": 3,
        "title": "Challenge 2 (Practice)",
        "published": True,
        "ciphertext": "GUVF VF N FRPERG ZRFFNTR",
        "plaintext": "THIS IS A SECRET MESSAGE",
        "tips": "This is a ROT13 cipher - each letter is shifted by 13 positions.",
        "points_reward": 10,
        "release_time": datetime(2025, 12, 29, 21, 0),
        "closing_time": datetime(2025, 12, 29, 21, 40)
    },
    {
        "id": 4,
        "title": "Challenge 3 (Practice)",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 15,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 5,
        "title": "Challenge 4",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 20,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 6,
        "title": "Challenge 5",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 20,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 7,
        "title": "Challenge 6",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 25,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 8,
        "title": "Challenge 7",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 25,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 9,
        "title": "Challenge 8",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 30,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 10,
        "title": "Challenge 9",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 30,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 11,
        "title": "Challenge 10",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 35,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 12,
        "title": "Challenge 11",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 35,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 13,
        "title": "Challenge 12",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 40,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 14,
        "title": "Challenge 13",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 40,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 15,
        "title": "Challenge 14",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 45,
        "release_time": None,
        "closing_time": None
    },
    {
        "id": 16,
        "title": "Challenge 15",
        "published": False,
        "ciphertext": "",
        "plaintext": "",
        "tips": "",
        "points_reward": 50,
        "release_time": None,
        "closing_time": None
    },
]

with app.app_context():
    # Clear existing challenges
    Challenges.query.delete()
    
    # Add new challenges
    for data in challenges_data:
        challenge = Challenges(
            id=data["id"]-1,  # Adjusting ID to be zero-based
            title=data["title"],
            published=data["published"],
            ciphertext=data["ciphertext"],
            plaintext=data["plaintext"],
            tips=data["tips"],
            points_reward=data["points_reward"],
            release_time=data["release_time"],
            closing_time=data["closing_time"]
        )
        db.session.add(challenge)
    
    db.session.commit()
    print(f"Successfully added {len(challenges_data)} challenges!")
    
    # Show summary
    published = Challenges.query.filter_by(published=True).count()
    unpublished = Challenges.query.filter_by(published=False).count()
    print(f"Published: {published}, Unpublished: {unpublished}")
