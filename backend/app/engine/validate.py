from app.models import Purchase, Situation, ValidationError


def validate(sit: Situation, purchase: Purchase | None = None) -> list[ValidationError]:
    raise NotImplementedError
