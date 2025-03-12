import json
import matplotlib.pyplot as plt
from datetime import datetime


def generate_report():
    with open('perf_report.json') as f:
        data = json.load(f)
    
    benchmarks = {}
    for test in data['benchmarks']:
        name = test['name'].split('[')[0]
        params = test['params']
        time = test['stats']['mean']
        
        if name not in benchmarks:
            benchmarks[name] = {'params': [], 'times': []}
        benchmarks[name]['params'].append(params)
        benchmarks[name]['times'].append(time)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for name, data in benchmarks.items():
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(data['times'])), data['times'])
        plt.xticks(range(len(data['params'])), data['params'], rotation=45)
        plt.ylabel('执行时间 (秒)')
        plt.title(f'{name} 性能基准测试')
        plt.tight_layout()
        plt.savefig(f'perf_{name}_{timestamp}.png')
        plt.close()

if __name__ == '__main__':
    generate_report()