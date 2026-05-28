"""
Rutas de autenticación y perfil de usuario.
Firebase gestiona el registro/login; aquí solo exponemos lectura y actualización de perfil.
"""

from fastapi import APIRouter, Depends
from google.cloud import firestore

from app.api.deps import CurrentUID, CurrentUser, DB
from app.core.responses import ok
from app.models.user import User
from app.utils.timestamps import utcnow_iso

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me(user: CurrentUser):
    """Retorna el perfil completo del usuario autenticado."""
    return ok(user.model_dump(by_alias=True))


@router.put("/profile")
async def update_profile(
    payload: dict,
    uid: CurrentUID,
    db: DB,
):
    """
    Actualiza campos editables del perfil: displayName, photoURL, role.
    Firebase Auth gestiona email y contraseña — no se tocan aquí.
    """
    ALLOWED = {"displayName", "photoURL", "role"}
    update_data = {k: v for k, v in payload.items() if k in ALLOWED}
    update_data["updatedAt"] = utcnow_iso()

    ref = db.collection("users").document(uid)
    doc = await ref.get()
    if not doc.exists:
        # Primera vez que accede al backend — crear perfil básico
        update_data.setdefault("createdAt", utcnow_iso())
        await ref.set(update_data, merge=True)
    else:
        await ref.update(update_data)

    updated = await ref.get()
    user = User.from_firestore(uid, updated.to_dict())
    return ok(user.model_dump(by_alias=True))
