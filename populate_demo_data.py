from app import create_app
from app.db import close_db, get_db, populate_demo_data


app = create_app()


with app.app_context():
    db = get_db()
    populate_demo_data(db)
    db.commit()
    close_db()
