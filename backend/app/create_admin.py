from getpass import getpass
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import User
from app.security import hash_password

def main():
    Base.metadata.create_all(bind=engine)
    username = input("Usuario administrador (sin espacios): ").strip()
    if not username or " " in username:
        raise SystemExit("El usuario no puede estar vacío ni contener espacios.")
    password = getpass("Contraseña robusta: ")
    confirm = getpass("Confirmar contraseña: ")
    if len(password) < 14:
        raise SystemExit("Use una contraseña de al menos 14 caracteres.")
    if password != confirm:
        raise SystemExit("Las contraseñas no coinciden.")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == username)):
            raise SystemExit("Ese usuario ya existe.")
        db.add(User(username=username, password_hash=hash_password(password), role="ADMIN", is_active=True))
        db.commit()
    print("Administrador creado. Guarde sus credenciales en el gestor autorizado.")

if __name__ == "__main__":
    main()
