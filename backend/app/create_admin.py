from getpass import getpass
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import User, Role
from app.security import hash_password


def _asegurar_rol(db, nombre: str) -> Role:
    rol = db.scalar(select(Role).where(Role.name == nombre))
    if rol is None:
        rol = Role(name=nombre)
        db.add(rol)
        db.flush()
    return rol


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
        _asegurar_rol(db, "ADMIN")
        db.add(User(username=username, password_hash=hash_password(password), role="ADMIN", is_active=True))
        db.commit()
    print("Administrador creado. Guarde sus credenciales en el gestor autorizado.")


if __name__ == "__main__":
    main()
