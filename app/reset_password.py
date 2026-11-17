from getpass import getpass

from pwdlib import PasswordHash
from sqlalchemy import select

from database import SessionLocal
from models import User

password_hash = PasswordHash.recommended()

username = input("Usuario: ")
nueva = getpass("Nueva contraseña: ")
confirmar = getpass("Repite la contraseña: ")

if nueva != confirmar:
    raise SystemExit("Las contraseñas no coinciden")
if len(nueva) < 8:
    raise SystemExit("Usa al menos 8 caracteres")

db = SessionLocal()
user = db.scalar(select(User).where(User.username == username))
if user is None:
    raise SystemExit("Ese usuario no existe")
user.hashed_password = password_hash.hash(nueva)
db.commit()
db.close()
print("Contraseña actualizada")