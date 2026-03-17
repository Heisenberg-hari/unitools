import json
import logging
import os

logger = logging.getLogger("unitools")
_client = None
_init_attempted = False


def _initialize_firestore_client():
    global _client, _init_attempted
    if _client is not None:
        return _client
    if _init_attempted:
        return None
    _init_attempted = True

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    if not service_account_json and not service_account_path:
        logger.info("Firebase audit disabled: no credentials configured.")
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if service_account_json:
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate(service_account_path)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        _client = firestore.client()
        logger.info("Firebase Firestore client initialized for audit logging.")
        return _client
    except Exception as exc:
        logger.warning("Firebase audit initialization failed: %s", exc)
        return None


def log_operation_event(operation, user):
    client = _initialize_firestore_client()
    if client is None:
        return
    try:
        payload = {
            "operation_id": operation.id,
            "user_id": getattr(user, "id", None),
            "username": getattr(user, "username", ""),
            "tool_name": operation.tool_name,
            "file_names": operation.file_names,
            "total_file_size": int(operation.total_file_size or 0),
            "status": operation.status,
            "created_at": operation.created_at.isoformat() if operation.created_at else None,
        }
        client.collection("operations").add(payload)
    except Exception as exc:
        logger.warning("Firebase audit write failed: %s", exc)
