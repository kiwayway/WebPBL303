import click

from .extensions import db
from .models import Role, User


def register_cli(app):
    @app.cli.command("create-admin")
    @click.argument("email")
    @click.argument("name")
    @click.password_option()
    def create_admin(email, name, password):
        """Buat akun admin: flask create-admin EMAIL NAMA"""
        email = email.strip().lower()
        if len(password) < 8:
            click.echo("Password minimal 8 karakter")
            return
        if User.query.filter_by(email=email).first():
            click.echo("Email sudah terdaftar")
            return
        user = User(email=email, name=name, role=Role.admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin {email} berhasil dibuat")