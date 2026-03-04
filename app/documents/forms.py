from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class FillOficioForm(FlaskForm):
    numero_solicitud = StringField(
        "N° Solicitud",
        validators=[DataRequired(message="Ingresa el número de solicitud."), Length(max=60)],
    )

    # Guardamos como texto "dd-mm-aaaa" porque así lo usa flatpickr.
    fecha_solicitud = StringField(
        "Fecha",
        validators=[DataRequired(message="Selecciona una fecha (dd-mm-aaaa)."), Length(min=10, max=10)],
    )

    tenor_literal = TextAreaField(
        "Tenor literal (editable)",
        validators=[DataRequired(message="Ingresa el tenor literal."), Length(max=5000)],
    )

    respuesta = TextAreaField(
        "Respuesta / Observación",
        validators=[DataRequired(message="Ingresa la respuesta."), Length(max=5000)],
    )

    guardar_pdf = BooleanField("Guardar PDF en el repositorio", default=True)