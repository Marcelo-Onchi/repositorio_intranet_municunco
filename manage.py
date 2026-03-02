from app import create_app
from app.extensions import db
from app import models  # noqa: F401  (para que Flask shell detecte modelos)

app = create_app()

@app.shell_context_processor
def _shell_context():
    return {"db": db, **models.__dict__}