"""Inicialización de Firebase Admin SDK y cliente Firestore async."""

import json
import os

import firebase_admin
from firebase_admin import auth, credentials
from google.cloud import firestore
from google.oauth2 import service_account
from loguru import logger

from app.core.config import settings

_firebase_app: firebase_admin.App | None = None
_db: firestore.AsyncClient | None = None


def _build_credentials() -> credentials.Base:
    """Construye las credenciales Firebase desde archivo o variables de entorno."""
    path = settings.FIREBASE_CREDENTIALS_PATH

    if os.path.isfile(path):
        logger.info(f"Firebase: usando credenciales desde archivo → {path}")
        return credentials.Certificate(path)

    # Fallback: construir desde variables de entorno
    if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_CLIENT_EMAIL:
        private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
        service_account_info = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        logger.info("Firebase: usando credenciales desde variables de entorno.")
        return credentials.Certificate(service_account_info)

    raise RuntimeError(
        "No se encontraron credenciales Firebase. "
        "Define FIREBASE_CREDENTIALS_PATH o FIREBASE_PROJECT_ID + FIREBASE_CLIENT_EMAIL + FIREBASE_PRIVATE_KEY."
    )


def init_firebase() -> None:
    """Inicializa Firebase Admin SDK (idempotente). Registra advertencia si faltan credenciales."""
    global _firebase_app
    if _firebase_app is not None:
        return

    try:
        cred = _build_credentials()
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK inicializado.")
    except RuntimeError as exc:
        logger.warning(f"Firebase no configurado: {exc}. El servidor arranca en modo sin credenciales.")


def get_firestore_client() -> firestore.AsyncClient:
    """Devuelve el cliente Firestore async (singleton)."""
    global _db
    if _db is None:
        path = settings.FIREBASE_CREDENTIALS_PATH

        if os.path.isfile(path):
            with open(path) as f:
                sa_info = json.load(f)
            sa_credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=["https://www.googleapis.com/auth/datastore"],
            )
            _db = firestore.AsyncClient(
                project=sa_info.get("project_id", settings.FIREBASE_PROJECT_ID),
                credentials=sa_credentials,
            )
        elif settings.FIREBASE_PROJECT_ID and settings.FIREBASE_CLIENT_EMAIL:
            private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
            sa_credentials = service_account.Credentials.from_service_account_info(
                {
                    "type": "service_account",
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "client_email": settings.FIREBASE_CLIENT_EMAIL,
                    "private_key": private_key,
                    "token_uri": "https://oauth2.googleapis.com/token",
                },
                scopes=["https://www.googleapis.com/auth/datastore"],
            )
            _db = firestore.AsyncClient(
                project=settings.FIREBASE_PROJECT_ID,
                credentials=sa_credentials,
            )
        else:
            raise RuntimeError("No se pueden inicializar las credenciales de Firestore.")

        logger.info("Cliente Firestore async inicializado.")
    return _db


def verify_token(id_token: str) -> dict:
    """Verifica el JWT de Firebase Auth y devuelve el payload decodificado."""
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except auth.ExpiredIdTokenError:
        raise ValueError("Token expirado.")
    except auth.InvalidIdTokenError as e:
        raise ValueError(f"Token inválido: {e}")
    except Exception as e:
        raise ValueError(f"Error al verificar token: {e}")
