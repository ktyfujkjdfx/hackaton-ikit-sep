from app.models import Dashboard, Purchase, Situation


def build_dashboard(sit: Situation, purchase: Purchase | None) -> Dashboard:
    raise NotImplementedError
