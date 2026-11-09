"""Hash de contraseñas con bcrypt (costo 12, según ARQUITECTURA.md §7.1)."""
import bcrypt

COSTO_BCRYPT = 12


class BcryptHasher:
    def hashear(self, contrasena: str) -> str:
        return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt(rounds=COSTO_BCRYPT)).decode("utf-8")

    def verificar(self, contrasena: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(contrasena.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            # Hash con formato inválido en la base: se trata como contraseña incorrecta
            return False