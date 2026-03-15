def default_model_params():
    return {
        "loss_function": "RMSE",
        "eval_metric": "RMSE",
        "iterations": 1000,
        "learning_rate": 0.05,
        "depth": 8,
        "verbose": 100,
        "allow_writing_files": False,
        "random_seed": 42,
    }
