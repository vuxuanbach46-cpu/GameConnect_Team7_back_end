from sqlalchemy.orm import Session

from app.models.report import Report


def create_report(
    db: Session,
    reporter_id: int,
    target_type: str,
    target_id: int,
    reason: str,
    description: str | None = None,
):
    report = Report(
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        description=description,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
