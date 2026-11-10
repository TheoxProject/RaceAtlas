"""Expose actual import audit evidence without converting synthetic samples to completeness."""

from sqlalchemy import func, select

from raceatlas.models import ImportRun, ImportWindow
from raceatlas.serialization import timestamp


def coverage_document(session, state):
    latest = session.scalar(
        select(ImportRun)
        .where(ImportRun.catalog_order > state.audit_floor)
        .order_by(ImportRun.catalog_order.desc())
        .limit(1)
    )
    last_success = session.scalar(
        select(ImportRun.finished_at)
        .where(
            ImportRun.status == "success",
            ImportRun.finished_at.is_not(None),
            ImportRun.catalog_order > state.audit_floor,
        )
        .order_by(ImportRun.catalog_order.desc())
        .limit(1)
    )
    if last_success is None:
        last_success = session.scalar(
            select(func.max(ImportRun.finished_at)).where(
                ImportRun.status == "success", ImportRun.catalog_order <= state.audit_floor
            )
        )
    if latest is None:
        legacy = session.scalar(select(ImportRun.id).limit(1)) is not None
        return {
            "status": "incomplete" if legacy else "unknown",
            "intrinsic_exhaustiveness": "unknown",
            "last_successful_sync_at": timestamp(last_success),
            "windows": [],
            "requested_from": None,
            "requested_to": None,
            "departments": [],
            "note": (
                "Audits historiques sans ordre d'exécution fiable ; nouveau contrôle requis."
                if legacy
                else "Aucune synchronisation contrôlée ; "
                "les fixtures ne prouvent pas la couverture FFC."
            ),
        }
    windows = session.scalars(
        select(ImportWindow)
        .where(ImportWindow.run_id == latest.id)
        .order_by(ImportWindow.requested_from, ImportWindow.requested_department, ImportWindow.id)
    ).all()
    documents = []
    for window in windows:
        coherent = (
            1 <= (window.requested_to - window.requested_from).days + 1 <= 14
            and window.requested_from == window.effective_from
            and window.requested_to == window.effective_to
            and window.requested_department == window.effective_department
            and window.displayed_count == window.distinct_keys
        )
        status = "consistent_sample" if coherent and window.status == "success" else "incomplete"
        documents.append(
            {
                "requested_from": window.requested_from.isoformat(),
                "requested_to": window.requested_to.isoformat(),
                "effective_from": window.effective_from.isoformat(),
                "effective_to": window.effective_to.isoformat(),
                "requested_department": window.requested_department,
                "effective_department": window.effective_department,
                "displayed_count": window.displayed_count,
                "distinct_keys": window.distinct_keys,
                "status": status,
                "reason": "; ".join(window.diagnostics)
                or ("Contrôle incomplet." if status == "incomplete" else None),
            }
        )
    sampled = (
        latest.status == "success"
        and latest.finished_at is not None
        and documents
        and all(window["status"] == "consistent_sample" for window in documents)
    )
    return {
        "status": "consistent_sample" if sampled else "incomplete",
        "intrinsic_exhaustiveness": "unknown",
        "last_successful_sync_at": timestamp(last_success),
        "windows": documents,
        "requested_from": min((window["requested_from"] for window in documents), default=None),
        "requested_to": max((window["requested_to"] for window in documents), default=None),
        "departments": sorted({window.requested_department for window in windows}),
        "note": "Fenêtres déclarées uniquement, sans continuité déduite de leur enveloppe. "
        + (
            "Audit synthétique hors réseau ; aucune complétude FFC réelle établie."
            if latest.synthetic
            else "Contrôles techniques bornés ; exhaustivité intrinsèque inconnue."
        ),
    }
