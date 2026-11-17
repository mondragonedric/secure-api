from getpass import getpass
from pwdlib import PasswordHash

from database import SessionLocal
from models import User

password_hash = PasswordHash.recommended()

username = input("Usuario: ")
password = getpass("Contraseña: ")

db = SessionLocal()
user = User(
    username=username,
    hashed_password=password_hash.hash(password),
    role="admin",
)
db.add(user)
db.commit()
db.close()
print("Admin creado")