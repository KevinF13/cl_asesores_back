from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import engine, get_db
from models import Base, Usuario, RegistroKPI
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date as date_type
import logging

# Inicializar Base de Datos y Logs
Base.metadata.create_all(bind=engine)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gestión Comercial - Farmacid S.A.")

# Configuración de Seguridad
SECRET_KEY = "F@rmacid_Secret_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # En producción, restringe esto
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# SCHEMAS
# =========================

class RegistroSchema(BaseModel):
    kpi: str

    # OBLIGATORIOS
    razon_social: str = Field(...)
    a_quien_visito: str = Field(...)
    desarrollo_visita: str = Field(...)

    # OPCIONALES
    nombre_comercial: Optional[str] = ""
    area: Optional[str] = ""
    telefono: Optional[str] = ""
    pendientes: Optional[str] = ""

    # KPIs Numéricos
    clientes_nuevos: int = 0
    prospectos_new: int = 0
    num_clientes_visitados: int = 0
    llamadas_clientes: int = 0
    llamadas_cobranzas: int = 0

    # KPIs Monetarios
    us_venta: float = 0.0
    us_cobro: float = 0.0
    viajes: float = 0.0
    alimentacion: float = 0.0

    # Tiempo y Planificación
    fecha_ingreso: date_type
    hora_ingreso: str
    fecha_prox_visita: Optional[str] = ""

    @field_validator("razon_social", "a_quien_visito", "desarrollo_visita")
    @classmethod
    def validar_campos_obligatorios(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Este campo es obligatorio")
        return value.strip()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    rol: str
    nombre: Optional[str] = None
    username: str
    id: int
    activo: bool


# =========================
# FUNCIONES AUXILIARES
# =========================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_by_username(db: Session, username: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Usuario:
    user = get_user_by_username(db, username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta al administrador.",
        )

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username is None or user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(Usuario).filter(
        Usuario.id == user_id,
        Usuario.username == username
    ).first()

    if not user:
        raise credentials_exception

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    return user


def get_current_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    return current_user


# =========================
# ENDPOINT: LOGIN
# =========================

@app.post("/token", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)

    # Actualizar updated_at al iniciar sesión
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": user.username,
            "rol": user.rol,
            "id": user.id,
            "nombre": user.nombre,
            "activo": user.activo
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "rol": user.rol,
        "nombre": user.nombre,
        "username": user.username,
        "id": user.id,
        "activo": user.activo
    }


# =========================
# ENDPOINT: USUARIO ACTUAL
# =========================

@app.get("/api/me")
def read_users_me(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "rol": current_user.rol,
        "nombre": current_user.nombre,
        "activo": current_user.activo,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }


# =========================
# ENDPOINT: GUARDAR KPI
# =========================

@app.post("/api/guardar-kpi")
async def guardar_kpi(
    data: RegistroSchema,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        datos_para_db = data.model_dump()

        # Procesar Hora: str -> time object
        try:
            hora_obj = datetime.strptime(datos_para_db["hora_ingreso"], "%H:%M").time()
        except ValueError:
            hora_obj = datetime.strptime(datos_para_db["hora_ingreso"], "%H:%M:%S").time()

        datos_para_db["hora_ingreso"] = hora_obj

        nuevo_reg = RegistroKPI(usuario_id=current_user.id, **datos_para_db)

        db.add(nuevo_reg)
        db.commit()
        db.refresh(nuevo_reg)

        return {
            "status": "success",
            "message": f"Registro de {data.kpi} guardado con éxito",
            "usuario": current_user.nombre
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error en /guardar-kpi: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


# =========================
# ENDPOINT: ADMIN KPIS
# =========================

@app.get("/api/admin/kpis")
def get_admin_kpis(
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    try:
        results = db.query(RegistroKPI, Usuario.nombre).join(
            Usuario, RegistroKPI.usuario_id == Usuario.id
        ).all()

        data = []
        for reg, nombre in results:
            item = {c.name: getattr(reg, c.name) for c in reg.__table__.columns}

            item["fecha_ingreso"] = str(item["fecha_ingreso"]) if item.get("fecha_ingreso") else None
            item["hora_ingreso"] = str(item["hora_ingreso"]) if item.get("hora_ingreso") else None
            item["asesor_nombre"] = nombre

            # Conversión explícita para frontend
            item["us_venta"] = float(item.get("us_venta") or 0)
            item["us_cobro"] = float(item.get("us_cobro") or 0)
            item["viajes"] = float(item.get("viajes") or 0)
            item["alimentacion"] = float(item.get("alimentacion") or 0)

            item["clientes_nuevos"] = int(item.get("clientes_nuevos") or 0)
            item["prospectos_new"] = int(item.get("prospectos_new") or 0)
            item["num_clientes_visitados"] = int(item.get("num_clientes_visitados") or 0)
            item["llamadas_clientes"] = int(item.get("llamadas_clientes") or 0)
            item["llamadas_cobranzas"] = int(item.get("llamadas_cobranzas") or 0)

            data.append(item)

        return data

    except Exception as e:
        logger.error(f"Error en /admin/kpis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al recuperar datos del servidor"
        )