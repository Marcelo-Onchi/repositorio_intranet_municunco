from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class FillOficioForm(FlaskForm):
    # Tipo de oficio (plantilla)
    oficio_tipo = SelectField(
        "Tipo de oficio",
        choices=[],
        validators=[DataRequired()],
    )

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

    # Categoría para guardado (solo si guardar_pdf=True)
    # - coerce=int para que venga como int desde el select
    category_id = SelectField(
        "Categoría para guardar",
        coerce=int,
        choices=[],
        validators=[Optional()],
    )

    def validate(self, extra_validators=None) -> bool:
        ok = super().validate(extra_validators=extra_validators)
        if not ok:
            return False

        if bool(self.guardar_pdf.data):
            # 0 => "— Selecciona —"
            if int(self.category_id.data or 0) == 0:
                self.category_id.errors.append("Selecciona una categoría para guardar el PDF.")
                return False

        return True