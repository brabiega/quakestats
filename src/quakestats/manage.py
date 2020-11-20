from passlib.hash import (
    pbkdf2_sha256,
)


def set_admin_password(db, password):
    assert password
    assert len(password) > 3
    hashpass = pbkdf2_sha256.hash(password)
    result = db.user.update_one(
        {"username": "admin"},
        {"$set": {"username": "admin", "password": hashpass}},
        upsert=True,
    )
    return result
