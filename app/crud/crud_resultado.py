from datetime import datetime, timedelta
from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.schemas import PlanCreate, PlanUpdate, EjercicioCreate, EjercicioUpdate, Plan, UmbralUpdate, UmbralCreate, ResultadoCreate, ResultadoUpdate, \
    Graficas
from app.schemas.graficas import grafico1, grafico2, grafico3, grafico4


class CRUDResultado(CRUDBase[tbl_historico_valores, ResultadoCreate, ResultadoUpdate]):

    def create_with_owner(
            self, db: Session, *, db_obj: tbl_umbrales, obj_in: ResultadoCreate,
    ) -> tbl_historico_valores:
        obj_in_data = obj_in.dict()

        resultado = tbl_historico_valores(**obj_in_data, fkUmbral=db_obj.id, umbral=db_obj)
        db.add(resultado)
        db.commit()
        db.refresh(resultado)
        return resultado

    def get_multi_valores(
            self, db: Session, *, umbral: int, skip: int = 0, limit: int = 100
    ) -> List[tbl_historico_valores]:
        return db.query(tbl_historico_valores).filter(tbl_historico_valores.fkUmbral == umbral).offset(skip).limit(limit).all()

    def get_graficas(selfself, db: Session, user: int, profesional:int) -> Graficas:
        result = Graficas()
        grafica3 = []
        grafica1 = []
        grafica4 = []
        grafica5 = []
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0, )
        fecha3dias = today - timedelta(days=3)
        fecha30dias = today - timedelta(days=30)
        # Lista de planes y planes actuales del usuario asignados por el entrenador
        sql_text = text("""
            select distinct te.fkPlan, max(te.fldDDia), min(te.fldDDia)
            from tbl_ejercicio te
            left join tbl_planes tp on (tp.id = te.fkPlan)
            left join tbl_asignado ta on (tp.id = ta.fkPlan)
            where ta.fkUsuario = """+str(user)+""" and ta.fkAsignador = """+str(profesional)+""" and te.fldDDia is not null
            group by te.fkPlan
        """)
        res = db.execute(sql_text)
        planes = "("
        planesAct = "("
        for row in res:
            if(len(planes) > 1):
                planes = planes + ", "
            planes = planes + str(row[0])
            if row[1] >= today >= row[2]:
                if (len(planesAct) > 1):
                    planesAct = planesAct + ", "
                planesAct = planesAct + str(row[0])
        planes = planes + ")"
        planesAct = planesAct + ")"

        if planes == "()":
            return result

        # Grafica 1: Relacion entre ejercicios realizados los 3 ultimos dias.
        sql_text = text("""
                            select count(*), tm.id, tm.fldSName
                            from tbl_historico_valores thv
                            left join tbl_umbrales tu on (tu.id = thv.fkUmbral)
                            left join tbl_ejercicio te on (te.id = tu.fkEjercicio)
                            left join tbl_model tm on (tm.id = te.fkEjercicio)
                            left join tbl_planes tp on (tp.id = te.fkPlan)
                            left join tbl_asignado ta on (ta.fkPlan = tp.id)
                            where tu.fldFValor <= thv.fldFValor and thv.fldDTimeFecha >= '"""+str(fecha3dias)+"""' and tp.id in """+str(planes)+"""
                            group by tm.id, tm.fldSName
                        """)
        res = db.execute(sql_text)
        for row in res:
            aux = grafico1()
            aux.ejercicio = row[2]
            aux.repeticiones = row[0]
            aux.id_ejercicio = row[1]
            grafica1.append(aux)
        result.grafico1 = grafica1
        # Grafica 4: Lista de repeticiones por ejercicio y dia en el ultimo mes
        sql_text = text("""
            select count(*), tm.id, tm.fldSName, te.fldDDia
            from tbl_historico_valores thv
            left join tbl_umbrales tu on (tu.id = thv.fkUmbral)
            left join tbl_ejercicio te on (te.id = tu.fkEjercicio)
            left join tbl_model tm on (tm.id = te.fkEjercicio)
            left join tbl_planes tp on (tp.id = te.fkPlan)
            left join tbl_asignado ta on (ta.fkPlan = tp.id)
            where tu.fldFValor <= thv.fldFValor and thv.fldDTimeFecha >= '""" + str(fecha30dias) + """' and tp.id in """ + str(planes) + """
            group by tm.id, tm.fldSName, te.fldDDia
        """)
        res = db.execute(sql_text)
        for row in res:
            aux = grafico4()
            aux.ejercicios = row[2]
            aux.repeticiones = row[0]
            aux.id_ejercicio = row[1]
            aux.dia = row[3]
            grafica4.append(aux)
        result.grafico4 = grafica4

        if planesAct == "()":
            return result

        # Grafica 2: Relacion entre intentos y exitos en el plan actual.
        grafica2 = grafico2()
        sql_text = text("""
                            select count(*)
                            from tbl_historico_valores thv
                            left join tbl_umbrales tu on (tu.id = thv.fkUmbral)
                            left join tbl_ejercicio te on (te.id = tu.fkEjercicio)
                            where te.fkPlan in """+str(planesAct)+"""
                        """)
        res = db.execute(sql_text)
        for row in res:
            grafica2.totales = row[0]
        sql_text = text("""
                            select count(*)
                            from tbl_historico_valores thv
                            left join tbl_umbrales tu on (tu.id = thv.fkUmbral)
                            left join tbl_ejercicio te on (te.id = tu.fkEjercicio)
                            where te.fkPlan in """ + str(planesAct) + """ and thv.fldFValor >= tu.fldFValor
                        """)
        res = db.execute(sql_text)
        for row in res:
            grafica2.correctas = row[0]

        # Grafica 3: Lista de objetivos repeticiones correctas e incorrectas para el plan actual
        sql_text = text("""
                                    select count(*)
                                    from tbl_historico_valores thv
                                    left join tbl_umbrales tu on (tu.id = thv.fkUmbral)
                                    left join tbl_ejercicio te on (te.id = tu.fkEjercicio)
                                    where te.fkPlan in """ + str(planesAct) + """
                                """)
        res = db.execute(sql_text)

        # Grafica 5: Relacion entre intentos y exitos en el plan actual.


        return result


resultado = CRUDResultado(tbl_historico_valores)
