import os

from envs.loader import load_project_env


def start_run(*, enabled, project, entity=None, name=None, tags=None):
    if not enabled:
        return None

    load_project_env()

    import wandb

    api_key = os.getenv("WANDB_API_KEY")
    if api_key:
        wandb.login(key=api_key)

    return wandb.init(
        project=project,
        entity=entity,
        name=name,
        tags=list(tags or []),
    )


def log_metrics(run, metrics, step=None):
    if run is None:
        return
    if step is None:
        run.log(metrics)
        return
    run.log(metrics, step=step)


def update_summary(run, summary):
    if run is None:
        return
    run.summary.update(summary)


def finish_run(run):
    if run is None:
        return
    run.finish()
