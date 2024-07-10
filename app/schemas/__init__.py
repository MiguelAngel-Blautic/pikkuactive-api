from .user import User, UserCreate, UserUpdate, UserDetails
from .token import Token, TokenPayload, ResumenEstadistico
from .plan import Plan, PlanCreate, PlanUpdate, PlanDetalle, EjercicioDetalle, EntrenamientoDetalle
from .resultados import RegistroEjercicio, RegistroEjercicioDB, TipoDato, Resultado, ResultadoBD
from .ejercicio import Ejercicio, EjercicioCreate, EjercicioUpdate, EjercicioTipos
from .serie import Serie, SerieCreate, SerieUpdate, Seriecompleta
from .bloque import Bloque, BloqueCreate, BloqueUpdate, Bloquecompleto
from .entrenamiento import Entrenamiento, EntrenamientoCreate, EntrenamientoUpdate, EntrenamientoCompleto