from app.models import GoalPlan, Situation


def goal_plan(sit: Situation, extra: int = 0) -> GoalPlan | None:
    raise NotImplementedError
