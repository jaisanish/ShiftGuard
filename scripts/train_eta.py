import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from backend.app.ml.eta.train import train_eta_model

def main():
    p=argparse.ArgumentParser(); p.add_argument('--tasks',type=Path,default=Path('data/synthetic/task_history.csv'))
    p.add_argument('--telemetry',type=Path,default=Path('data/synthetic/telemetry_history.csv'))
    p.add_argument('--artifact',type=Path,default=Path('backend/app/ml/eta/artifacts/shiftguard_eta_v1.joblib'))
    p.add_argument('--metadata',type=Path,default=Path('backend/app/ml/eta/artifacts/shiftguard_eta_v1.metadata.json'))
    a=p.parse_args(); print(json.dumps(train_eta_model(a.tasks,a.telemetry,a.artifact,a.metadata),indent=2))
if __name__=='__main__': main()
