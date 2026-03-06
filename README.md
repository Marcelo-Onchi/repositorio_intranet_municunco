📂 Intranet Municunco — Repositorio de Documentos

Sistema interno de gestión documental desarrollado para la Municipalidad de Cunco, diseñado para centralizar archivos institucionales, organizar documentos por categorías y gestionar recordatorios asociados a usuarios mediante integración con Google Calendar.

El sistema está desarrollado en Flask (Python) con arquitectura modular basada en Blueprints, utilizando PostgreSQL como base de datos principal y preparado para ejecutarse dentro de la infraestructura interna municipal.

📊 Estado del Proyecto
Módulo	Estado
Autenticación (Login / Logout)	✅ Implementado
Dashboard con estadísticas	✅ Implementado
Gestión de documentos	✅ Implementado
Subida de archivos	✅ Implementado
Sistema de recordatorios	✅ Implementado
Integración Google Calendar	✅ Implementado
Panel de administración	🟡 Base funcional
🧰 Stack Tecnológico
Backend

Python 3.12+

Flask

SQLAlchemy

Flask-Login

Flask-WTF

Base de Datos

PostgreSQL 16+

Frontend

HTML5

CSS modular (base.css + pages.css)

JavaScript Vanilla

Lucide Icons

Integraciones

Google Calendar API

OAuth 2.0

🏗 Arquitectura

El proyecto utiliza Flask Blueprints para separar cada módulo funcional del sistema.

app/
 ├── admin/              # Panel administrativo
 ├── auth/               # Autenticación de usuarios
 ├── documents/          # Gestión de documentos
 ├── calendar_bp/        # Integración Google Calendar
 ├── static/
 │    ├── css/
 │    │     ├── base.css
 │    │     └── pages.css
 │    └── js/
 │          └── base.js
 ├── templates/
 │    ├── admin/
 │    ├── auth/
 │    ├── calendar/
 │    ├── documents/
 │    ├── base.html
 │    └── dashboard.html
 ├── models.py
 ├── extensions.py
 ├── config.py
 └── __init__.py

instance/        # Archivos de instancia (no versionado)
uploads/         # Documentos subidos por usuarios (no versionado)

run.py
requirements.txt
⚙️ Entornos
Desarrollo

Base de datos: PostgreSQL

URL local:

http://127.0.0.1:5000

Sistema operativo actual: Windows

Producción

Base de datos: PostgreSQL 16+

Sistema operativo: Ubuntu Server

Infraestructura: Servidor interno municipal

Acceso: HTTPS

🚀 Instalación (Entorno Local)
1️⃣ Clonar repositorio
git clone <url-del-repositorio>
cd repositorio_intranet_municunco
2️⃣ Crear entorno virtual
python -m venv venv

Activar entorno virtual:

Windows

venv\Scripts\activate

Linux / Mac

source venv/bin/activate
3️⃣ Instalar dependencias
pip install -r requirements.txt
4️⃣ Configurar variables de entorno

Crear archivo:

.env

Basarse en:

.env.example
5️⃣ Ejecutar aplicación
python run.py

Abrir navegador:

http://127.0.0.1:5000/auth/login
🔐 Variables de Entorno

El sistema utiliza variables definidas en .env.

Ejemplo:

SECRET_KEY=

FLASK_ENV=development
FLASK_DEBUG=1

DATABASE_URL=postgresql://usuario:password@localhost:5432/municunco_db

UPLOAD_DIR=uploads

ADMIN_EMAIL=
ADMIN_PASSWORD=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

APP_TIMEZONE=America/Santiago

⚠️ El archivo .env nunca debe subirse al repositorio.

📂 Gestión de Archivos

Los documentos subidos por los usuarios se almacenan en:

uploads/

Estructura típica:

uploads/
 ├── documents/
 └── generated/

Este directorio no se versiona en Git.

🔒 Seguridad

Este repositorio es privado y de uso interno municipal.

No se versionan los siguientes elementos:

.env
instance/
uploads/
*.db
credenciales OAuth

El acceso al repositorio se gestiona mediante invitación privada en GitHub.

🧪 Buenas Prácticas del Proyecto

El sistema fue desarrollado siguiendo principios de mantenibilidad:

Arquitectura modular mediante Flask Blueprints

Separación clara entre backend y frontend

Configuración mediante variables de entorno

Preparado para infraestructura on-premise municipal

Código estructurado para mantenimiento institucional

🧾 Convención de Commits

Formato utilizado:

tipo: descripción

Tipos de commit utilizados:

Tipo	Uso
feat	nueva funcionalidad
fix	corrección de error
style	cambios visuales
refactor	reorganización interna
docs	documentación

Ejemplos:

feat: agregar integración Google Calendar
feat: implementar sistema de recordatorios por usuario
style: mejorar layout dashboard
fix: corregir callback OAuth Google
docs: actualizar README del proyecto
📅 Próximos Objetivos

Mejoras en el panel administrativo

Sistema de permisos más granular

Registro de auditoría de acciones

Optimización para infraestructura municipal

Mejoras de rendimiento y escalabilidad

👨‍💻 Responsable del Proyecto

Marcelo Montoya Mellado
Unidad de Informática
Municipalidad de Cunco

Año: 2026

📄 Licencia

Proyecto de uso interno institucional.
No destinado para distribución pública.