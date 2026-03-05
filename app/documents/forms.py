from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class FillOficioForm(FlaskForm):
    numero_solicitud = StringField(
        "N° Solicitud",
        validators=[DataRequired(), Length(min=3, max=40)],
    )

    fecha_solicitud = StringField(
        "Fecha",
        validators=[DataRequired(), Length(min=8, max=12)],
        description="En el documento queda como dd/mm/aaaa.",
    )

    de_nombre = StringField(
        "DE: Nombre",
        validators=[DataRequired(), Length(min=3, max=120)],
    )

    de_cargo = StringField(
        "DE: Cargo",
        validators=[DataRequired(), Length(min=3, max=120)],
    )

    a_nombre = StringField(
        "A: Nombre destinatario",
        validators=[DataRequired(), Length(min=3, max=120)],
    )

    tenor_literal = TextAreaField(
        "Tenor literal (editable)",
        validators=[DataRequired(), Length(min=1, max=6000)],
    )

    respuesta = TextAreaField(
        "Respuesta / Observación",
        validators=[DataRequired(), Length(min=1, max=6000)],
    )

    guardar_pdf = BooleanField("Guardar PDF en el repositorio")