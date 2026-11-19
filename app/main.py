from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from logger import logger
from models import Equipment, User
from rate_limit import esta_bloqueado, limpiar, registrar_fallo
from schemas import EquipmentCreate, EquipmentRead, UserCreate, UserRead
from security import (
    DUMMY_HASH,
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)

app = FastAPI(title="Secure API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "desconocida"

    restante = esta_bloqueado(ip)
    if restante > 0:
        logger.warning("LOGIN_BLOQUEADO ip=%s restante=%ss", ip, restante)
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Intenta más tarde.",
            headers={"Retry-After": str(restante)},
        )

    user = db.scalar(select(User).where(User.username == form.username))
    hash_a_verificar = user.hashed_password if user else DUMMY_HASH
    clave_ok = verify_password(form.password, hash_a_verificar)
    if user is None or not clave_ok:
        bloqueada = registrar_fallo(ip)
        logger.warning("LOGIN_FALLIDO usuario=%r ip=%s", form.username, ip)
        if bloqueada:
            logger.warning("IP_BLOQUEADA ip=%s", ip)
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    limpiar(ip)
    logger.info("LOGIN_OK usuario=%r rol=%s ip=%s", user.username, user.role, ip)
    token = create_access_token(user.username, user.role)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users", response_model=list[UserRead])
def listar_usuarios(
    db: Session = Depends(get_db), user: User = Depends(require_role("admin"))
):
    return db.scalars(select(User).order_by(User.id)).all()


@app.post("/users", response_model=UserRead)
def crear_usuario(
    item: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    nuevo = User(
        username=item.username,
        hashed_password=hash_password(item.password),
        role=item.role.value,
    )
    db.add(nuevo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    db.refresh(nuevo)
    logger.info(
        "USUARIO_CREADO por=%r nuevo=%r rol=%s",
        user.username,
        nuevo.username,
        nuevo.role,
    )
    return nuevo


@app.get("/equipment", response_model=list[EquipmentRead])
def listar_equipos(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return db.scalars(select(Equipment).order_by(Equipment.id)).all()


@app.post("/equipment", response_model=EquipmentRead)
def crear_equipo(
    item: EquipmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    nuevo = Equipment(**item.model_dump())
    db.add(nuevo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El número de serie ya existe")
    db.refresh(nuevo)
    logger.info(
        "EQUIPO_CREADO por=%r id=%s serial=%r",
        user.username,
        nuevo.id,
        nuevo.serial_number,
    )
    return nuevo


@app.put("/equipment/{equipo_id}", response_model=EquipmentRead)
def actualizar_equipo(
    equipo_id: int,
    item: EquipmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    equipo = db.get(Equipment, equipo_id)
    if equipo is None:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    for campo, valor in item.model_dump().items():
        setattr(equipo, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El número de serie ya existe")
    db.refresh(equipo)
    logger.info("EQUIPO_ACTUALIZADO por=%r id=%s", user.username, equipo.id)
    return equipo


@app.delete("/equipment/{equipo_id}")
def borrar_equipo(
    equipo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    equipo = db.get(Equipment, equipo_id)
    if equipo is None:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    serial = equipo.serial_number
    db.delete(equipo)
    db.commit()
    logger.info(
        "EQUIPO_ELIMINADO por=%r id=%s serial=%r", user.username, equipo_id, serial
    )
    return {"mensaje": "Equipo eliminado"}