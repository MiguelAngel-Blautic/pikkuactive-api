import json
from typing import Any, List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
import requests
from app.db.session import SessionLocal
import firebase_admin
from firebase_admin import ml
from firebase_admin import credentials
import tensorflow as tf

router = APIRouter()
serverToken = 'AAAAyNDqQ8c:APA91bEETtU_JtV_41C71VDqsr3bsZvRlBaDFHezOO0zm1Iac5UhUURVylMJVPCOAmTev6D-oCq-qWmtT7EjzJm9jEHp5BgreYK8nVfK5wqKKuzqg4SD-mblR-QM0XtYTlzNKPRX7Ppm'
