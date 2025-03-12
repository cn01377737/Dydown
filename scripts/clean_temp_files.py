import os
import time
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).parent.parent

def clean_pycache():
    for root, dirs, _ in os.walk(PROJECT_ROOT):
        if '__pycache__' in dirs:
            pycache_path = Path(root) / '__pycache__'
            print(f'Removing {pycache_path}')
            shutil.rmtree(pycache_path)

def clean_old_logs(days=3):
    log_dir = PROJECT_ROOT / 'logs'
    if not log_dir.exists():
        return
    
    cutoff = time.time() - days * 86400
    
    for log_file in log_dir.glob('*.log'):
        if log_file.stat().st_mtime < cutoff:
            print(f'Removing old log: {log_file}')
            log_file.unlink()

if __name__ == '__main__':
    clean_pycache()
    clean_old_logs()
    print('Cleanup completed successfully')