from app.models import Event, Purchase, Situation


def events(sit: Situation, purchase: Purchase | None) -> list[Event]:
    raise NotImplementedError
