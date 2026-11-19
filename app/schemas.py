from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EquipmentStatus(str, Enum):
    disponible = "disponible"
    asignado = "asignado"
    en_reparacion = "en_reparacion"
    baja = "baja"


class EquipmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    serial_number: str = Field(min_length=1, max_length=100)
    status: EquipmentStatus = EquipmentStatus.disponible


class EquipmentRead(EquipmentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserRole(str, Enum):
    admin = "admin"
    tecnico = "tecnico"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.tecnico


class UserRead(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)