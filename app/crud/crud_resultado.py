from datetime import datetime, timedelta
from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import tbl_device, tbl_movement
from app.models.tbl_ejercicio import tbl_ejercicio, tbl_umbrales, tbl_historico_valores
from app.schemas import PlanCreate, PlanUpdate, EjercicioCreate, EjercicioUpdate, Plan, UmbralUpdate, UmbralCreate, ResultadoCreate, ResultadoUpdate, \
    Grafica, Grafica2, Grafica1, Grafica3, Grafica4, Grafica4Aux, Grafica5


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

    def get_graficas(
            self, db: Session, *, user: int, profesional: int
    ) -> Grafica:
        g1 = []
        g2 = Grafica2(total_correcto=0, total=0)
        g3 = []
        g4 = []
        g5 = []

        hoy = datetime.utcnow()
        fecha7dias = hoy - timedelta(days=7)
        fecha30dias = hoy - timedelta(days=30)

        # Grafica 1: Cantidad de repeticiones correctas por ejercicio en los ultimos 7 dias
        sql_text = text("""
            Select m.id, m.fldSName, count(*)
            from tbl_historico_valores hv 
                left join tbl_umbrales u on (hv.fkUmbral = u.id)
                left join tbl_ejercicio e on (e.id = u.fkEjercicio)
                left join tbl_model m on (m.id = e.fkEjercicio)
                left join tbl_planes s on (s.id = e.fkPlan)
                join tbl_asignado a on (a.fkPlan = s.id)
            where a.fkUsuario = """+str(user)+""" and s.fkCreador = """+str(profesional)+""" and hv.fldDTimeFecha < '"""+str(fecha7dias)+"""'
                and u.fldFValor <= hv.fldFvalor 
            group by m.id, m.fldSName
            """)
        res = db.execute(sql_text)
        for row in res:
            g1.append(Grafica1(id_ejercicio=row[0], nombre_ejercicio=row[1], repeticiones=row[2]))

        # Grafica 2: Relacion de intentos correctos frente a totales en los ultimos 7 dias
        sql_text = text("""
            select count(*) 
            from tbl_historico_valores hv 
                left join tbl_umbrales u on (u.id = hv.fkUmbral)
                left join tbl_ejercicio e on (e.id = u.fkEjercicio)
                left join tbl_planes s on (s.id = e.fkPlan)
                join tbl_asignado a on (a.fkPlan = s.id)
            where a.fkUsuario = """+str(user)+""" and s.fkCreador = """+str(profesional)+""" and hv.fldDTimeFecha < '"""+str(fecha7dias)+"""'
            """)
        res = db.execute(sql_text)
        for row in res:
            g2.total = row[0]
        sql_text = text("""
                    select count(*) 
                    from tbl_historico_valores hv 
                        left join tbl_umbrales u on (u.id = hv.fkUmbral)
                        left join tbl_ejercicio e on (e.id = u.fkEjercicio)
                        left join tbl_planes s on (s.id = e.fkPlan)
                        join tbl_asignado a on (a.fkPlan = s.id)
                    where a.fkUsuario = """ + str(user) + """ and s.fkCreador = """ + str(profesional) + """ and
                     hv.fldDTimeFecha < '""" + str(fecha7dias) + """' and u.fldFValor <= hv.fldFvalor 
                    """)
        res = db.execute(sql_text)
        for row in res:
            g2.total_correcto = row[0]

        # Grafica 3: Cantidad de repeticiones correctas por ejercicio en el plan actual
        sql_text = text("""
            select distinct aux.id
            from (select p.id as id, max(e.fldDDia) as fin, min(e.fldDDia) as inicio
                from tbl_ejercicio e
                    left join tbl_planes p on (e.fkPlan = p.id)
                    left join tbl_asignado a on (a.fkPlan = p.id)
                where a.fkUsuario = """+str(user)+""" and p.fkCreador = """+str(profesional)+""" and e.fldDDia is not null
                group by p.id
            
                ) as aux
            where '"""+str(hoy)+"""' between aux.inicio and aux.fin
            """)
        res = db.execute(sql_text)
        plan = 0
        for row in res:
            plan = row[0]

        if plan != 0:
            sql_text = text("""
                select p.id, p.fldSNombre,
                    (select count(*)
                    from tbl_historico_valores hv
                        left join tbl_umbrales u on (hv.fkUmbral = u.id)
                        left join tbl_ejercicio e on (e.id = u.fkEjercicio)
                    where e.fkPlan = p.id),
                    (select count(*)
                    from tbl_historico_valores hv
                        left join tbl_umbrales u on (hv.fkUmbral = u.id)
                        left join tbl_ejercicio e on (e.id = u.fkEjercicio)
                    where u.fldFValor <= hv.fldFvalor and e.fkPlan = p.id)
                from tbl_planes p
                where p.id = """+str(plan)+"""
                """)
            res = db.execute(sql_text)
            for row in res:
                g3.append(Grafica3(id_ejercicio=row[0], nombre_ejercicio=row[1], intentos=row[2], correctos=row[3]))

        # Grafica 4: Cantidad de repeticiones por ejercicio y dia en los ultimos 30 dias
        sql_text = text("""
            Select distinct hv.fldDTimeFecha
            from tbl_historico_valores hv 
                left join tbl_umbrales u on (hv.fkUmbral = u.id)
                left join tbl_ejercicio e on (e.id = u.fkEjercicio)
                left join tbl_model m on (m.id = e.fkEjercicio)
                left join tbl_planes s on (s.id = e.fkPlan)
                join tbl_asignado a on (a.fkPlan = s.id)
            where a.fkUsuario = """+str(user)+""" and s.fkCreador = """+str(profesional)+""" and hv.fldDTimeFecha < '"""+str(fecha30dias)+"""'
                and u.fldFValor <= hv.fldFvalor 
            """)
        res = db.execute(sql_text)
        for row in res:
            g4aux = []
            sql_text1 = text("""
                Select m.id, m.fldSName, count(*)
                from tbl_historico_valores hv 
                    left join tbl_umbrales u on (hv.fkUmbral = u.id)
                    left join tbl_ejercicio e on (e.id = u.fkEjercicio)
                    left join tbl_model m on (m.id = e.fkEjercicio)
                    left join tbl_planes s on (s.id = e.fkPlan)
                    join tbl_asignado a on (a.fkPlan = s.id)
                where a.fkUsuario = """+str(user)+""" and s.fkCreador = """+str(profesional)+""" and hv.fldDTimeFecha = '"""+str(row[0])+"""'
                    and u.fldFValor <= hv.fldFvalor 
                group by m.id, m.fldSName
                """)
            res1 = db.execute(sql_text1)
            for row1 in res1:
                g4aux.append(Grafica4Aux(id_ejercicio=row1[0], nombre_ejercicio=row1[1], repeticiones=row1[2]))
            g4.append(Grafica4(fecha=row[0], ejercicios=g4aux))

        # Grafica 5: Objetivos y cantidad de repeticiones por planes
        sql_text = text("""
            Select p.id, p.fldSNombre, sum(e.fldNRepeticiones), 
                (select count(*) 
                from tbl_historico_valores hv 
                    left join tbl_umbrales u on (u.id = hv.fkUmbral) 
                where u.fkEjercicio = e.id and u.fldFValor <= hv.fldFvalor and hv.fldDTimeFecha < '"""+str(fecha30dias)+"""')
            from tbl_ejercicio e
                left join tbl_model m on (m.id = e.fkEjercicio)
                left join tbl_planes p on (p.id = e.fkPlan)
                join tbl_asignado a on (a.fkPlan = p.id)
            where a.fkUsuario = """+str(user)+""" and p.fkCreador = """+str(profesional)+""" and e.fldDDia > '"""+str(fecha30dias)+"""'
            group by p.id, p.fldSNombre;
            """)
        res = db.execute(sql_text)
        for row in res:
            g5.append(Grafica5(id_plan=row[0], nombre_plan=row[1], objetivo=row[2], repeticiones=row[3]))

        # Entrega de resultados
        result = Grafica(grafica1=g1, grafica2=g2, grafica3=g3, grafica4=g4, grafica5=g5)
        return result


resultado = CRUDResultado(tbl_historico_valores)
