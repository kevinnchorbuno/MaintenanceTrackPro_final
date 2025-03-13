# add_user.py
from app import app, db
from models import User

# Define the new boss user details
USERNAME = "boss"
PASSWORD = "boss123"
ROLE = "boss"


# Function to add a new boss user
def add_boss_user():
    with app.app_context():
        existing_user = User.query.filter_by(username=USERNAME).first()
        if existing_user:
            print(f"User '{USERNAME}' already exists in the database.")
            return

        new_user = User(username=USERNAME, role=ROLE)
        new_user.set_password(PASSWORD)

        db.session.add(new_user)
        db.session.commit()

        print(f"User '{USERNAME}' with role '{ROLE}' added successfully.")


if __name__ == "__main__":
    add_boss_user()