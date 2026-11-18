![tests](https://github.com/mondragonedric/secure-api/actions/workflows/tests.yml/badge.svg)
# Secure API

API REST de inventario de equipos informáticos, creada para practicar seguridad en backend: autenticación, autorización por roles, hash de contraseñas, validación, logs y límite de intentos de login.

Este es un proyecto personal de aprendizaje.

## Stack

Python 3.13 · FastAPI · PostgreSQL 16 · SQLAlchemy · Docker Compose · JWT (PyJWT) · Argon2 (pwdlib) · pytest

## Qué implementa

- **Autenticación:** `POST /login` entrega un token JWT firmado con caducidad.
- **Autorización por roles:** `admin` puede todo; `tecnico` puede ver, crear y editar equipos, pero no borrar ni administrar usuarios.
- **Contraseñas:** solo se guarda el hash (Argon2 con salt), nunca la contraseña.
- **Validación:** esquemas Pydantic (nombres, estados permitidos, longitud de contraseña) y número de serie único a nivel de base de datos.
- **Logs de seguridad:** inicios de sesión correctos y fallidos, altas, cambios y bajas de equipos, accesos denegados.
- **Límite de intentos:** 5 logins fallidos por IP bloquean esa IP durante 5 minutos (`429`).
- **Respuestas que no filtran información:** usuario inexistente y contraseña incorrecta devuelven el mismo error.
- **Docker:** la API corre como usuario sin privilegios y la base de datos solo escucha en `127.0.0.1`.

## Endpoints

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/health` | público |
| POST | `/login` | público |
| GET | `/users` | admin |
| POST | `/users` | admin |
| GET | `/equipment` | usuario autenticado |
| POST | `/equipment` | usuario autenticado |
| PUT | `/equipment/{id}` | usuario autenticado |
| DELETE | `/equipment/{id}` | admin |

Documentación interactiva en `http://127.0.0.1:8000/docs`.

## Cómo correrlo

Requisitos: Docker Desktop.

1. Copia `.env.example` a `.env` y cambia los valores. Para generar la `SECRET_KEY`:

   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Levanta la base y la API:

   ```
   docker compose up -d --build
   ```

3. Crea las tablas y el primer administrador (no hay registro público a propósito):

   ```
   docker compose exec api python create_tables.py
   docker compose exec api python create_admin.py
   ```

4. Abre `http://127.0.0.1:8000/docs`, pulsa **Authorize** e inicia sesión.

## Pruebas

Las pruebas usan una base de datos aparte (`<POSTGRES_DB>_test`) para no tocar los datos reales.

```
docker compose exec db psql -U <POSTGRES_USER> <POSTGRES_DB> -c "CREATE DATABASE <POSTGRES_DB>_test;"
pip install -r requirements.txt pytest httpx
pytest -v
```

## Limitaciones conocidas

- El límite de intentos vive en memoria: se reinicia con el servidor y no sirve con varias instancias. Dentro de Docker, todas las peticiones llegan con la misma IP interna.
- Las tablas se crean con un script, sin migraciones (por ejemplo Alembic).
- Sin HTTPS, sin renovación ni revocación de tokens.
- Pensada para aprender, no para producción.