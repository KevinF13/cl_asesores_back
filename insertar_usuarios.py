from database import SessionLocal
from models import Usuario
from passlib.context import CryptContext
from getpass import getpass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def crear_usuario():
    db = SessionLocal()
    try:
        print("\n=== CREAR USUARIO ===")
        username = input("Usuario: ").strip()
        nombre = input("Nombre: ").strip()
        rol = input("Rol (admin/asesor): ").strip().lower()
        password = getpass("Contraseña: ").strip()

        existe = db.query(Usuario).filter(Usuario.username == username).first()
        if existe:
            print(f"⚠️ El usuario '{username}' ya existe.")
            return

        nuevo_usuario = Usuario(
            username=username,
            password_hash=pwd_context.hash(password),
            rol=rol,
            nombre=nombre
        )
        db.add(nuevo_usuario)
        db.commit()
        print(f"✅ Usuario '{username}' creado correctamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario: {e}")
    finally:
        db.close()


def listar_usuarios():
    db = SessionLocal()
    try:
        print("\n=== LISTA DE USUARIOS ===")
        usuarios = db.query(Usuario).all()

        if not usuarios:
            print("No hay usuarios registrados.")
            return

        for i, u in enumerate(usuarios, start=1):
            print(f"{i}. Usuario: {u.username} | Nombre: {u.nombre} | Rol: {u.rol}")
    except Exception as e:
        print(f"❌ Error al listar usuarios: {e}")
    finally:
        db.close()


def cambiar_password():
    db = SessionLocal()
    try:
        print("\n=== CAMBIAR CONTRASEÑA ===")
        username = input("Usuario: ").strip()
        usuario = db.query(Usuario).filter(Usuario.username == username).first()

        if not usuario:
            print(f"⚠️ No existe el usuario '{username}'.")
            return

        nueva_password = getpass("Nueva contraseña: ").strip()
        confirmar_password = getpass("Confirmar nueva contraseña: ").strip()

        if nueva_password != confirmar_password:
            print("⚠️ Las contraseñas no coinciden.")
            return

        usuario.password_hash = pwd_context.hash(nueva_password)
        db.commit()
        print(f"✅ Contraseña actualizada para '{username}'.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al cambiar contraseña: {e}")
    finally:
        db.close()


def editar_usuario():
    db = SessionLocal()
    try:
        print("\n=== EDITAR USUARIO ===")
        username = input("Usuario a editar: ").strip()
        usuario = db.query(Usuario).filter(Usuario.username == username).first()

        if not usuario:
            print(f"⚠️ No existe el usuario '{username}'.")
            return

        print(f"Nombre actual: {usuario.nombre}")
        nuevo_nombre = input("Nuevo nombre (Enter para no cambiar): ").strip()

        print(f"Rol actual: {usuario.rol}")
        nuevo_rol = input("Nuevo rol (Enter para no cambiar): ").strip().lower()

        if nuevo_nombre:
            usuario.nombre = nuevo_nombre
        if nuevo_rol:
            usuario.rol = nuevo_rol

        db.commit()
        print(f"✅ Usuario '{username}' actualizado correctamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al editar usuario: {e}")
    finally:
        db.close()


def eliminar_usuario():
    db = SessionLocal()
    try:
        print("\n=== ELIMINAR USUARIO ===")
        username = input("Usuario a eliminar: ").strip()
        usuario = db.query(Usuario).filter(Usuario.username == username).first()

        if not usuario:
            print(f"⚠️ No existe el usuario '{username}'.")
            return

        confirmacion = input(f"¿Seguro que deseas eliminar a '{username}'? (s/n): ").strip().lower()
        if confirmacion != "s":
            print("Operación cancelada.")
            return

        db.delete(usuario)
        db.commit()
        print(f"✅ Usuario '{username}' eliminado.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al eliminar usuario: {e}")
    finally:
        db.close()


def insertar_usuarios_iniciales():
    db = SessionLocal()
    usuarios_lista = [
        {"user": "Admin", "pass": "Admin", "rol": "admin", "nombre": "Administrador General"},
        {"user": "mguaman", "pass": "mguaman123", "rol": "asesor", "nombre": "M. Guaman"},
        {"user": "aatiaja", "pass": "aatiaja123", "rol": "asesor", "nombre": "A. Atiaja"},
        {"user": "dibanez", "pass": "dibanez123", "rol": "asesor", "nombre": "D. Ibanez"}
    ]
    try:
        for u in usuarios_lista:
            existe = db.query(Usuario).filter(Usuario.username == u["user"]).first()
            if not existe:
                nuevo_usuario = Usuario(
                    username=u["user"],
                    password_hash=pwd_context.hash(u["pass"]),
                    rol=u["rol"],
                    nombre=u["nombre"]
                )
                db.add(nuevo_usuario)
                print(f"✅ Usuario {u['user']} creado.")
            else:
                print(f"⚠️ El usuario {u['user']} ya existe.")
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar usuarios iniciales: {e}")
    finally:
        db.close()


def menu():
    while True:
        print("\n" + "=" * 40)
        print("   SISTEMA DE GESTIÓN DE USUARIOS")
        print("=" * 40)
        print("1. Insertar usuarios iniciales")
        print("2. Crear usuario")
        print("3. Listar usuarios")
        print("4. Cambiar contraseña")
        print("5. Editar usuario")
        print("6. Eliminar usuario")
        print("7. Salir")
        print("=" * 40)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            insertar_usuarios_iniciales()
        elif opcion == "2":
            crear_usuario()
        elif opcion == "3":
            listar_usuarios()
        elif opcion == "4":
            cambiar_password()
        elif opcion == "5":
            editar_usuario()
        elif opcion == "6":
            eliminar_usuario()
        elif opcion == "7":
            print("👋 Saliendo del sistema...")
            break
        else:
            print("⚠️ Opción inválida. Intenta de nuevo.")


if __name__ == "__main__":
    menu()