# Repositorio Intranet Municunco (Privado Municipal)

Sistema interno de la Municipalidad de Cunco para gestión de documentos y recordatorios por usuario.

Proyecto desarrollado en Flask, con arquitectura modular basada en blueprints y preparado para trabajar con SQLite en desarrollo y PostgreSQL en entorno productivo municipal.

---

## Estado Actual

- ✅ Autenticación (Login / Logout)
- ✅ Dashboard con estadísticas generales
- ✅ Módulo Documentos (explorar y subir archivos)
- ✅ Módulo Admin (base funcional)
- ✅ UI unificada (base.html + base.css + base.js)
- 🟡 Integración Google Calendar (OAuth 2.0) pendiente credenciales oficiales

---

## Stack Tecnológico

- Python 3.12+
- Flask
- SQLAlchemy
- SQLite (entorno desarrollo actual)
- PostgreSQL 16+ (planificado para producción)
- Google Calendar API (OAuth 2.0)

---

## Entornos

### Desarrollo (Actual)
- Base de datos: SQLite (`local.db`)
- URL local: http://127.0.0.1:5000
- Sistema operativo: Windows

### Producción (Planificado)
- Base de datos: PostgreSQL 16+
- Servidor: Ubuntu Server (infraestructura municipal)
- Acceso vía HTTPS

---

## Instalación (Desarrollo Local)

### 1️⃣ Crear entorno virtual

python -m venv venv  
venv\Scripts\activate  
pip install -r requirements.txt  

### 2️⃣ Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto (NO se versiona).  
Basarse en `.env.example`.

### 3️⃣ Ejecutar aplicación

python run.py  

Acceder en navegador:

http://127.0.0.1:5000/auth/login

---

## Variables de Entorno

El proyecto utiliza un archivo `.env` con las siguientes variables:

- SECRET_KEY
- FLASK_ENV
- FLASK_DEBUG
- DATABASE_URL
- UPLOAD_DIR
- ADMIN_EMAIL
- ADMIN_PASSWORD
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI
- APP_TIMEZONE

⚠️ El archivo `.env` NO debe subirse al repositorio.

---

## Estructura del Proyecto

app/
 ├── admin/
 ├── auth/
 ├── documents/
 ├── calendar_bp/
 ├── static/
 │    ├── css/
 │    └── js/
 ├── templates/
 │    ├── admin/
 │    ├── auth/
 │    ├── calendar/
 │    ├── documents/
 │    ├── base.html
 │    └── dashboard.html
 ├── models.py
 ├── config.py
 └── extensions.py

instance/      (no versionado)
uploads/       (no versionado)
run.py
requirements.txt

---

## Seguridad y Buenas Prácticas

Este repositorio es privado y de uso interno municipal.

No se versionan:
- `.env`
- `instance/`
- `uploads/`
- bases locales (`*.db`)
- credenciales OAuth

El acceso al repositorio se gestiona mediante invitación en GitHub.

---

## Convención de Commits

- feat: nueva funcionalidad
- fix: corrección de error
- style: cambios visuales
- refactor: reorganización interna
- docs: documentación

Ejemplos:
feat: agregar conexión Google Calendar por usuario  
style: unificar layout base y sidebar  
fix: corregir callback OAuth  

---

## Próximos Objetivos

- Migración definitiva a PostgreSQL
- Configuración HTTPS en producción
- Control de permisos más granular
- Auditoría de acciones

---

## Responsable

Desarrollador: Marcelo Montoya Mellado  
Unidad de Informática  
Municipalidad de Cunco  
Año: 2026