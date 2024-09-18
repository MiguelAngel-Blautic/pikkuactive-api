from datetime import datetime
from statistics import mean
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy import text, Date
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1.endpoints import resultados
from app.core.config import settings
from app.models import tbl_user, tbl_entrena, tbl_planes, tbl_bloques, tbl_series, tbl_ejercicios, tbl_entrenamientos
from app.models.tbl_resultados import tbl_registro_ejercicios, tbl_resultados
from app.schemas import RegistroEjercicioDB, EjercicioTipos, ResumenEstadistico
from app.schemas.ejercicio import Resultado, EjercicioDetalles

router = APIRouter()


@router.get("/", response_model=List[EjercicioTipos])
def read_ejercicios_by_serie_server(
    serie_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_ejercicios_by_serie(serie_id=serie_id, db=db, current_user=current_user)
    db.close()
    return res


def read_ejercicios_by_serie(
        serie_id: int,
        db: Session,
        current_user: models.tbl_user,
) -> Any:
    if current_user.fkRol == 2:
        serie = db.query(tbl_series).get(serie_id)
        if not serie:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        bloque = db.query(tbl_bloques).get(serie.fkBloque)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if not plan:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == serie_id).all()
    else:
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkCreador == current_user.id).filter(tbl_ejercicios.fkSerie == serie_id).all()
    tipodatos = []
    res = []
    for e in ejercicios:
        tipos = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == e.id).all()
        for t in tipos:
            tipodatos.append(RegistroEjercicioDB(fkEjercicio=t.fkEjercicio, id=t.id, fkTipoDato=t.fkTipoDato))
        if e.fkModelo == 0:
            e.fkModelo = None
        res.append(EjercicioTipos(
            tipodatos=tipodatos,
            fkSerie=e.fkSerie,
            fldNOrden=e.fldNOrden,
            fldNDescanso=e.fldNDescanso,
            fldNRepeticiones=e.fldNRepeticiones,
            fldNDuracion=e.fldNDuracion,
            fldNDuracionEfectiva=e.fldNDuracionEfectiva,
            fldFVelocidad=e.fldFVelocidad,
            fldFUmbral=e.fldFUmbral,
            fkModelo=e.fkModelo,
            fldSToken=e.fldSToken,
            fldNDistancia=e.fldNDistancia,
            id=e.id,
            fldNErp=e.fldNErp,
            fldNPeso=e.fldNPeso
        ))
        tipodatos = []
    return res


def read_ejercicios_by_idDB(
    id: int,
    db: Session,
    current_user: models.tbl_user,
) -> Any:
    ejercicio = db.query(tbl_ejercicios).filter(tbl_ejercicios.id == id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="The exercise doesn't exist")
    if current_user.fkRol == 2:
        serie = db.query(tbl_series).get(ejercicio.fkSerie)
        if not serie:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        bloque = db.query(tbl_bloques).get(serie.fkBloque)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    return ejercicio

def read_ejercicios_by_id_serie_detalle(
    id: int,
    generico: int,
    db: Session
) -> Any:
    res = []
    ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == id).all()
    for ejercicio in ejercicios:
        ritmo = None
        distancia = None
        hr = None
        if generico == 0:
            ejerciciosConcretos = [ejercicio]
        else:
            ejerciciosConcretos = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkPadre == ejercicio.id).all()
        adherencias = []
        for ec in ejerciciosConcretos:
            adhPartial = 0
            registroRep = db.query(tbl_registro_ejercicios).filter(
                tbl_registro_ejercicios.fkEjercicio == ec.id).filter(
                tbl_registro_ejercicios.fkTipoDato == 2).first()
            if registroRep:
                results = db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroRep.id).all()
                if ec.fldNRepeticiones:
                    if len(results) > 0:
                        adhPartial = sum([r.fldFValor for r in results]) / ejercicio.fldNRepeticiones
                    else:
                        adhPartial = 0
            registroDist = db.query(tbl_registro_ejercicios).filter(
                tbl_registro_ejercicios.fkEjercicio == ec.id).filter(
                tbl_registro_ejercicios.fkTipoDato == 9).first()
            if registroDist:
                results = db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroDist.id).all()
                if len(results) > 0:
                    distancia = max([r.fldFValor for r in results])
                if ec.fldNDistancia:
                    if ec.fldNDistancia > 0:
                        if distancia:
                            adhPartial = distancia / ejercicio.fldNDistancia
            registroRitm = db.query(tbl_registro_ejercicios).filter(
                tbl_registro_ejercicios.fkEjercicio == ec.id).filter(
                tbl_registro_ejercicios.fkTipoDato == 8).first()
            if registroRitm:
                results = db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroRitm.id).all()
                if len(results) > 0:
                    ritmo = mean([r.fldFValor for r in results])
            registroHr = db.query(tbl_registro_ejercicios).filter(
                tbl_registro_ejercicios.fkEjercicio == ec.id).filter(
                tbl_registro_ejercicios.fkTipoDato == 3).first()
            if registroHr:
                results = db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == registroHr.id).all()
                if len(results) > 0:
                    hr = mean([r.fldFValor for r in results])
            adherencias.append(adhPartial)
        if len(adherencias) >= 1:
            adherencia = mean(adherencias)
        else:
            adherencia = 0
        res.append(EjercicioDetalles(
            fldNOrden=ejercicio.fldNOrden,
            fldNDescanso=ejercicio.fldNDescanso,
            fldNRepeticiones=ejercicio.fldNRepeticiones,
            fldNDuracion=ejercicio.fldNDuracion,
            fldFVelocidad=ejercicio.fldFVelocidad,
            fldFUmbral=ejercicio.fldFUmbral,
            fkModelo=ejercicio.fkModelo,
            fldSToken=ejercicio.fldSToken,
            id=ejercicio.id,
            adherencia=adherencia,
            fldNDistancia=ejercicio.fldNDistancia,
            items=[],
            tipo=5,
            completo=0,
            nombre="",
            duracion=ejercicio.fldNDuracion,
            fldFDistanceGoal=ejercicio.fldNDistancia,
            fldFRhythmGoal=ejercicio.fldFVelocidad,
            fldFRhythmMean=ritmo,
            fldFDistance=distancia,
            fldFHrMean=hr,
            fldNErp=ejercicio.fldNErp,
            fldNPeso=ejercicio.fldNPeso
            # fldFHrGoal=ejercicio.
        ))
    return res

@router.get("/{id}", response_model=schemas.EjercicioTipos)
def read_ejercicios_by_id_server(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    res = read_ejercicios_by_id(id=id, db=db, current_user=current_user)
    db.close()
    return res


def read_ejercicios_by_id(
        id: int,
        db: Session,
        current_user: models.tbl_user,
) -> Any:
    ejercicio = db.query(tbl_ejercicios).filter(tbl_ejercicios.id == id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="The exercise doesn't exist")
    if current_user.fkRol == 2:
        serie = db.query(tbl_series).get(ejercicio.fkSerie)
        if not serie:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        bloque = db.query(tbl_bloques).get(serie.fkBloque)
        if not bloque:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        entrenamiento = db.query(tbl_entrenamientos).get(bloque.fkEntrenamiento)
        if not entrenamiento:
            raise HTTPException(status_code=404, detail="The id doesn't exist")
        plan = db.query(tbl_planes).get(entrenamiento.fkPlan)
        if plan.fkCliente != current_user.id:
            raise HTTPException(status_code=401, detail="Not enought privileges")
    tipodatos = []
    tipos = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == ejercicio.id).all()
    repeticiones = 0
    for t in tipos:
        tipodatos.append(RegistroEjercicioDB(fkEjercicio=t.fkEjercicio, id=t.id, fkTipoDato=t.fkTipoDato))
        if t.fkTipoDato == 0:
            repeticiones = db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == t.id).count()
    res = EjercicioTipos(
        tipodatos=tipodatos,
        fkSerie=ejercicio.fkSerie,
        fldNOrden=ejercicio.fldNOrden,
        fldNDescanso=ejercicio.fldNDescanso,
        fldNRepeticiones=ejercicio.fldNRepeticiones,
        fldNDuracion=ejercicio.fldNDuracion,
        fldNDuracionEfectiva=ejercicio.fldNDuracionEfectiva,
        fldFVelocidad=ejercicio.fldFVelocidad,
        fldFUmbral=ejercicio.fldFUmbral,
        fkModelo=ejercicio.fkModelo,
        fldSToken=ejercicio.fldSToken,
        fldNDistancia=ejercicio.fldNDistancia,
        id=ejercicio.id,
        finalizado=repeticiones,
        fldNErp=ejercicio.fldNErp,
        fldNPeso=ejercicio.fldNPeso
    )
    return res


@router.post("/list", response_model=List[schemas.ResumenEstadistico])
def read_ejercicios_by_id_serie(
        serie: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    sql = text("""
        SELECT te.fkPadre, te2.id , sum(te.fldNRepeticioneS)
from tbl_ejercicios te
    join tbl_ejercicios te2 on (te2.id = te.fkPadre)
   WHERE te2.fkSerie = """+str(serie)+""" group by te.fkPadre; """)
    res = db.execute(sql)
    adherencia = 0
    for row in res:
        sql = text("""
        SELECT sum(tr.fldFValor)
            from tbl_resultados tr join tbl_registro_ejercicios tre on (tre.id = tr.fkRegistro) join tbl_ejercicios te on (te.id = tre.fkEjercicio)
            where te.fkPadre=""" + str(row[0]) + """ and tre.fkTipoDato = 2;""")
        total = db.execute(sql)
        for t in total:
            adherencia = (t[0] * 100) / row[2]
        entrada = ResumenEstadistico(
            tipo=5,
            nombre=row[1],
            adherencia=adherencia,
            completo=0,
            id=row[0],
        )
        response.append(entrada)
    db.close()
    return response


@router.post("/date/list")
def read_ejercicios_by_day(
        plan: int,
        fecha: datetime,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    sensors = []
    results = []
    sql = text("""
            select te.fkModelo, tr.fldDTime, ttd.fldFNombre, tr.fldFValor
    FROM tbl_resultados tr 
    	join tbl_registro_ejercicios tre on (tr.fkRegistro = tre.id)
    	join tbl_ejercicios te on (tre.fkEjercicio = te.id)
	    join tbl_series ts on (ts.id = te.fkSerie)
	    join tbl_bloques tb on (tb.id = ts.fkBloque)
	    join tbl_entrenamientos te2 on (te2.id = tb.fkEntrenamiento)
    	join tbl_tipo_datos ttd on (ttd.id = tre.fkTipoDato)
    WHERE te2.fkPlan = """+str(plan)+""" and date(te2.fldDDia) = date('"""+str(fecha)+"""') 
    order by te.fkModelo, ttd.fldFNombre, tr.fldDTime, tr.fldFValor; """)
    res = db.execute(sql)
    sens = ""
    date = ""
    for row in res:
        if sens == "":
            sens = row[2]
            date = row[0]
        if date != row[0]:
            sensors.append({"sensor": sens, "results": results})
            response.append({"time": date, "results": sensors})
            sensors = []
            results = []
            sens = row[2]
            date = row[0]
        if sens != row[2]:
            sensors.append({"sensor": sens, "results": results})
            results = []
            sens = row[2]
        results.append({"valor": row[3], "time": row[1]})
    if sens != "":
        sensors.append({"sensor": sens, "results": results})
        response.append({"time": date, "results": sensors})
    db.close()
    return response


@router.post("/dates")
def read_resultados_by_id_ejercicio(
        ejercicio: int,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    sensors = []
    results = []
    sql = text("""
        select date(tr.fldDTime), tr.fldDTime, ttd.fldFNombre, tr.fldFValor
FROM tbl_resultados tr 
	join tbl_registro_ejercicios tre on (tr.fkRegistro = tre.id)
	join tbl_ejercicios te on (tre.fkEjercicio = te.id)
	join tbl_tipo_datos ttd on (ttd.id = tre.fkTipoDato)
WHERE te.fkPadre = """+str(ejercicio)+"""
order by date(tr.fldDTime), ttd.fldFNombre, tr.fldDTime, tr.fldFValor; """)
    res = db.execute(sql)
    sens = ""
    date = ""
    for row in res:
        if sens == "":
            sens = row[2]
            date = row[0]
        if date != row[0]:
            sensors.append({"sensor": sens, "results": results})
            response.append({"time": date, "results": sensors})
            sensors = []
            results = []
            sens = row[2]
            date = row[0]
        if sens != row[2]:
            sensors.append({"sensor": sens, "results": results})
            results = []
            sens = row[2]
        results.append({"valor": row[3], "time": row[1]})
    sensors.append({"sensor": sens, "results": results})
    response.append({"time": date, "results": sensors})
    db.close()
    return response


@router.post("/resultsDate")
def read_resultados_by_date_plan(
        plan: int,
        fecha: datetime,
        current_user: models.tbl_user = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    response = []
    sensors = []
    results = []
    sql = text("""
        select te.id, tr.fldDTime, ttd.fldFNombre, tr.fldFValor
FROM tbl_resultados tr 
	join tbl_registro_ejercicios tre on (tr.fkRegistro = tre.id)
	join tbl_ejercicios te on (tre.fkEjercicio = te.id)
	join tbl_series ts on (ts.id = te.fkSerie)
	join tbl_bloques tb on (tb.id = ts.fkBloque)
	join tbl_entrenamientos ten on (ten.id = tb.fkEntrenamiento)
	join tbl_tipo_datos ttd on (ttd.id = tre.fkTipoDato)
WHERE ten.fkPlan = """+str(plan)+""" and date(tr.fldDTime) = date('"""+str(fecha.date())+"""')
order by date(tr.fldDTime), ttd.fldFNombre, tr.fldDTime, tr.fldFValor;""")
    res = db.execute(sql)
    sens = ""
    date = ""
    for row in res:
        if sens == "":
            sens = row[2]
            date = str(row[0])
        if date != str(row[0]):
            sensors.append({"sensor": sens, "results": results})
            response.append({"time": date, "results": sensors})
            sensors = []
            results = []
            sens = row[2]
            date = str(row[0])
        if sens != row[2]:
            sensors.append({"sensor": sens, "results": results})
            results = []
            sens = row[2]
        results.append({"valor": row[3], "time": row[1]})
    sensors.append({"sensor": sens, "results": results})
    response.append({"time": date, "results": sensors})
    db.close()
    return response


def read_valores_ejercicios(
    *,
    db: Session,
    serie: int
) -> List[Resultado]:
    ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == serie).all()
    res = []
    for e in ejercicios:
        if e.fldNRepeticiones is not None:
            dato = db.query(tbl_registro_ejercicios).filter(tbl_registro_ejercicios.fkEjercicio == e.id).filter(tbl_registro_ejercicios.fkTipoDato == 2).first()
            datos = db.query(tbl_resultados).filter(tbl_resultados.fkRegistro == dato.id).all()
            adherencia = len(datos) / e.fldNRepeticiones
            res.append(Resultado(id=e.id, adherencia=adherencia, completo=100, nombre=""))
        # res.append(Resultado(id=e.id, nombre=e.fld))
    return res


@router.post("/", response_model=schemas.Ejercicio)
def create_ejercicio(
    *,
    db: Session = Depends(deps.get_db),
    ejercicio_in: schemas.EjercicioCreate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Create new plan
    """
    ejercicios = read_ejercicios_by_serie(db=db, current_user=current_user, serie_id=ejercicio_in.fkSerie)
    newEjercicio = tbl_ejercicios(fkCreador=current_user.id,
                        fkSerie=ejercicio_in.fkSerie,
                        fldNDescanso=ejercicio_in.fldNDescanso,
                        fldNOrden=len(ejercicios)+1,
                        fldNRepeticiones=ejercicio_in.fldNRepeticiones,
                        fldNDuracion=ejercicio_in.fldNDuracion,
                        fldNDuracionEfectiva=ejercicio_in.fldNDuracionEfectiva,
                        fldFVelocidad=ejercicio_in.fldFVelocidad,
                        fldFUmbral=ejercicio_in.fldFUmbral,
                        fkModelo=ejercicio_in.fkModelo,
                        fldNDistancia=ejercicio_in.fldNDistancia,
                        fldSToken=ejercicio_in.fldSToken,
                        fldNErp=ejercicio_in.fldNErp,
                        fldNPeso=ejercicio_in.fldNPeso)
    db.add(newEjercicio)
    db.commit()
    db.refresh(newEjercicio)
    new = tbl_registro_ejercicios(fkTipoDato=0,
                                  fkEjercicio=newEjercicio.id)
    db.add(new)
    db.commit()
    for r in ejercicio_in.registros:
        new = tbl_registro_ejercicios(fkTipoDato=r,
                                      fkEjercicio=newEjercicio.id)
        db.add(new)
        db.commit()
    db.close()
    return newEjercicio


@router.put("/{id}", response_model=schemas.Ejercicio)
def update_ejercicio(
    *,
    id: int,
    db: Session = Depends(deps.get_db),
    ejercicio_in: schemas.EjercicioUpdate,
    current_user: models.tbl_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update plan.
    """
    ejercicio = read_ejercicios_by_idDB(id=id, db=db, current_user=current_user)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="The exercise doesn't exist")
    ejercicio.fldNDescanso = ejercicio_in.fldNDescanso
    ejercicio.fldNRepeticiones = ejercicio_in.fldNRepeticiones
    ejercicio.fldNDuracion = ejercicio_in.fldNDuracion
    ejercicio.fldNDuracionEfectiva=ejercicio_in.fldNDuracionEfectiva
    ejercicio.fldFVelocidad = ejercicio_in.fldFVelocidad
    ejercicio.fldFUmbral = ejercicio_in.fldFUmbral
    ejercicio.fkModelo = ejercicio_in.fkModelo
    ejercicio.fldSToken = ejercicio_in.fldSToken
    ejercicio.fldNDistancia = ejercicio_in.fldNDistancia
    db.commit()
    db.refresh(ejercicio)
    db.close()
    return ejercicio


@router.delete("/{id}")
def delete_ejericio(
    id: int,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    ejercicio = read_ejercicios_by_idDB(id=id, db=db, current_user=current_user)
    change_order(ejercicio.id, 0, current_user=current_user, db=db)
    db.delete(ejercicio)
    db.commit()
    db.close()
    return


@router.post("/orden", response_model=schemas.Ejercicio)
def change_order_server(
    ejercicio_id: int,
    new_posicion: int = 0,
    current_user: models.tbl_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    res = change_order(ejercicio_id, new_posicion, current_user, db)
    db.close()
    return res

def change_order(
        ejercicio_id: int,
        new_posicion: int,
        current_user: models.tbl_user,
        db: Session,
) -> Any:
    """
    Cambia la posicion de una serie
    """
    ejercicio = read_ejercicios_by_idDB(id=ejercicio_id, db=db, current_user=current_user)
    if new_posicion == 0:
        total_ejercicios = read_ejercicios_by_serie(serie_id=ejercicio.fkSerie, db=db, current_user=current_user)
        new_posicion = len(total_ejercicios) + 1
    if(new_posicion > ejercicio.fldNOrden):
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == ejercicio.fkSerie).filter(tbl_ejercicios.fldNOrden > ejercicio.fldNOrden).filter(tbl_ejercicios.fldNOrden <= new_posicion).all()
        for e in ejercicios:
            e.fldNOrden = e.fldNOrden - 1
        ejercicio.fldNOrden = new_posicion
    else:
        ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == ejercicio.fkSerie).filter(
            tbl_ejercicios.fldNOrden < ejercicio.fldNOrden).filter(tbl_ejercicios.fldNOrden >= new_posicion).all()
        for e in ejercicios:
            e.fldNOrden = e.fldNOrden + 1
        ejercicio.fldNOrden = new_posicion
    db.commit()
    db.refresh(ejercicio)
    return ejercicio

def clonar(
    old_serie: int,
    new_serie: int,
    db: Session,
) -> Any:
    ejercicios = db.query(tbl_ejercicios).filter(tbl_ejercicios.fkSerie == old_serie).all()
    for e in ejercicios:
        new = tbl_ejercicios(fkSerie=new_serie,
                            fldNDescanso=e.fldNDescanso,
                            fldNDuracion=e.fldNDuracion,
                            fldNDuracionEfectiva = e.fldNDuracionEfectiva,
                            fldNRepeticiones=e.fldNRepeticiones,
                            fldFVelocidad=e.fldFVelocidad,
                            fldFUmbral=e.fldFUmbral,
                            fldNOrden=e.fldNOrden,
                            fkModelo=e.fkModelo,
                            fldNDistancia=e.fldNDistancia,
                            fkCreador=e.fkCreador,
                            fldSToken=e.fldSToken,
                            fkPadre=e.id,
                            fldNErp=e.fldNErp,
                            fldNPeso=e.fldNPeso)
        db.add(new)
        db.commit()
        db.refresh(new)
        resultados.clonar(old_ejercicio=e.id, new_ejercicio=new.id, db=db)
    return




























