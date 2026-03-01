from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, MultipleFileField
from wtforms.validators import DataRequired, Optional


class UploadDocumentForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired()])
    description = TextAreaField("Descripción", validators=[Optional()])
    category_id = SelectField("Categoría", coerce=int, validators=[Optional()])
    fecha_documento = DateField("Fecha del documento", validators=[Optional()])
    files = MultipleFileField("Archivos", validators=[DataRequired()])


class FilterForm(FlaskForm):
    q = StringField("Buscar", validators=[Optional()])
    category_id = SelectField("Categoría", coerce=int, validators=[Optional()])
    desde = DateField("Desde", validators=[Optional()])
    hasta = DateField("Hasta", validators=[Optional()])