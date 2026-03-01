from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Optional, Length


class CreateUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    is_admin = BooleanField("Es admin", default=False)


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Nueva contraseña", validators=[DataRequired(), Length(min=6)])


class CategoryForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=80)])