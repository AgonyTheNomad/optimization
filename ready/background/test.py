import optuna

def objective(trial):
    x = trial.suggest_float("x", -10, 10)
    return (x - 2) ** 2

username = 'agony'
password = 'Jones917'
database_name = 'initial_db'
host = 'database-1.cfqiqso6ipei.us-east-2.rds.amazonaws.com'  # The endpoint from the AWS RDS instance
port = '5432'

DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{database_name}"


if __name__ == "__main__":

    storage = optuna.storages.RDBStorage(url=DATABASE_URL)

    # Create a study object
    study = optuna.create_study(study_name="example_study", storage=storage, load_if_exists=True)
    
    # Optimize the study, this will save and retrieve the study from the database
    study.optimize(objective, n_trials=10)

    print(f"Best trial: {study.best_trial.params['x']} with value: {study.best_trial.value}")
