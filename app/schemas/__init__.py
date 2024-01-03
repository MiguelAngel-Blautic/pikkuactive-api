from .model import Model, ModelCreate, ModelInDB, ModelUpdate
from .msg import Msg
from .plan import Plan, PlanCreate, PlanUpdate, PlanResumen
from .token import Token, TokenPayload
from .user import User, UserCreate, UserInDB, UserUpdate, UserComplete
from .movement import Movement, MovementCreate, MovementInDB, MovementUpdate
from .position import Position, PositionCreate, PositionInDB, PositionUpdate
from .device import Device, DeviceCreate, DeviceInDB, DeviceUpdate
from .capture import Capture, CaptureCreate, CaptureInDB, CaptureUpdate
from .mpu import Mpu, MpuCreate, MpuInDB, MpuUpdate
from .version import Version, VersionCreate, VersionInDB, VersionUpdate
from .asignado import Asignado, AsignadoCreate, AsignadoUpdate
from .entrena import Entrena, EntrenaCreate, EntrenaUpdate
from .ejercicio import Ejercicio, EjercicioCreate, EjercicioUpdate, EjercicioResumen
from .umbral import Umbral, UmbralCreate, UmbralUpdate
from .resultado import Resultado, ResultadoCreate, ResultadoUpdate
from .grafica import Grafica1, Grafica2, Grafica3, Grafica4Aux, Grafica5, Grafica4, Grafica, GraficaBase
