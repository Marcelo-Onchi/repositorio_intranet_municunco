from __future__ import annotations

import os

from dotenv import load_dotenv

from app import create_app
from app.extensions import db
from app.models import User


def main() -> None:
    load_dotenv()

    email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    password = (os.getenv("ADMIN_PASSWORD") or "").strip()

    if not email or not password:
        print("Falta ADMIN_EMAIL o ADMIN_PASSWORD en .env")
        return

    app = create_app()

    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(email=email).first()
        if not admin:
            admin = User(
                email=email,
                full_name="Administrador",
                is_admin=True,
                is_active=True,
            )
            admin.set_password(password)
            db.session.add(admin)
        else:
            admin.full_name = admin.full_name or "Administrador"
            admin.is_admin = True
            admin.is_active = True
            admin.set_password(password)

        db.session.commit()
        print(f"OK: Admin listo -> {email} / {password}")


if __name__ == "__main__":
    main()