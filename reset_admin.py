from __future__ import annotations

import os

from dotenv import load_dotenv

from app import create_app
from app.extensions import db
from app.models import User


def main() -> None:
    load_dotenv()

    admin_username = (os.getenv("ADMIN_USERNAME") or "admin").strip().lower()
    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    admin_password = (os.getenv("ADMIN_PASSWORD") or "").strip()

    if not admin_email or not admin_password:
        print("Falta ADMIN_EMAIL o ADMIN_PASSWORD en .env")
        return

    app = create_app()

    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(username=admin_username).first()
        if not admin:
            admin = User.query.filter_by(email=admin_email).first()

        if not admin:
            admin = User(
                username=admin_username,
                email=admin_email,
                full_name="Administrador",
                is_admin=True,
                is_active=True,
            )
            admin.set_password(admin_password)
            db.session.add(admin)
        else:
            admin.username = admin_username
            admin.email = admin_email
            admin.full_name = admin.full_name or "Administrador"
            admin.is_admin = True
            admin.is_active = True
            admin.set_password(admin_password)

        db.session.commit()
        print(f"OK: Admin listo -> usuario={admin_username} / pass={admin_password} / email={admin_email}")


if __name__ == "__main__":
    main()