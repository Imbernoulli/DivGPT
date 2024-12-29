import json
import ast
import numpy as np
from itertools import combinations
from tqdm import tqdm
import multiprocessing as mp
from functools import partial
from datasets import load_dataset
import sys
import signal
import contextlib
import time

class TimeoutException(Exception):
    pass

@contextlib.contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)

def run_test(code, entry_point, test_cases, timeout=1):
    namespace = {}
    results = {
        'passed': 0,
        'failed': 0,
        'error': 0,
        'timeout': 0,
        'total': len(test_cases)
    }
    
    try:
        with time_limit(timeout):
            exec(code, namespace)
        
        func = namespace[entry_point]
        
        for test in test_cases:
            try:
                with time_limit(timeout):
                    exec(test, namespace)
                print(f"✓ Test passed: {test}")
                results['passed'] += 1
            except TimeoutException:
                print(f"⏰ Timeout: {test}")
                results['timeout'] += 1
            except AssertionError:
                print(f"✗ Test failed: {test}")
                results['failed'] += 1
            except Exception as e:
                print(f"! Error running test {test}: {str(e)}")
                results['error'] += 1
                
    except TimeoutException:
        print(f"⏰ Timeout while executing code")
        results['timeout'] = len(test_cases)
    except Exception as e:
        print(f"! Error executing code: {str(e)}")
        results['error'] = len(test_cases)
        
    return results

def get_ast_nodes(code_str):
    """获取代码的AST节点集合"""
    try:
        tree = ast.parse(code_str)
        nodes = set()
        for node in ast.walk(tree):
            node_info = (type(node).__name__,)
            
            if isinstance(node, ast.Name):
                node_info += (node.id,)
            elif isinstance(node, ast.Num):
                node_info += (node.n,)
            elif isinstance(node, ast.Str):
                node_info += (node.s,)
            elif isinstance(node, ast.Compare):
                node_info += tuple(type(op).__name__ for op in node.ops)
            elif isinstance(node, ast.BinOp):
                node_info += (type(node.op).__name__,)
            
            nodes.add(node_info)
        return nodes
    except:
        return set()

def compute_ast_similarity_matrix(codes):
    """计算代码间的AST相似度矩阵"""
    num_codes = len(codes)
    similarity_matrix = np.zeros((num_codes, num_codes))
    
    ast_nodes_list = [get_ast_nodes(code) for code in codes]
    for i, j in combinations(range(num_codes), 2):
        intersection = len(ast_nodes_list[i] & ast_nodes_list[j])
        union = len(ast_nodes_list[i] | ast_nodes_list[j])
        sim = intersection / union if union != 0 else 0
        similarity_matrix[i,j] = similarity_matrix[j,i] = sim
    
    np.fill_diagonal(similarity_matrix, 1)
    return similarity_matrix

def select_diverse_codes(codes, n=32):
    """选择最不相似的n个代码样本"""
    if len(codes) <= n:
        return codes
    
    similarity_matrix = compute_ast_similarity_matrix(codes)
    
    selected_indices = [0]
    while len(selected_indices) < n:
        remaining_indices = list(set(range(len(codes))) - set(selected_indices))
        max_similarities = []
        
        for idx in remaining_indices:
            max_sim = max(similarity_matrix[idx][selected_indices])
            max_similarities.append((max_sim, idx))
        
        _, next_idx = min(max_similarities)
        selected_indices.append(next_idx)
    
    return [codes[i] for i in selected_indices]

def process_chunk(chunk, output_file, lock):
    """处理数据块并实时写入结果的函数"""
    for item in tqdm(chunk):
        item['resps'] = [i for i in item['resps'] if run_test(i["code"], i["entry_point"], i["test_cases"])['passed'] == i["total"]]
        if len(item['resps']) >= 1:
            diverse_codes = select_diverse_codes(item['resps'], n=32)
            diverse_item = {
                'query': item['query'],
                'gt_ans': item['gt_ans'],
                'diverse_responses': diverse_codes
            }
            with lock:
                with open(output_file, 'a', encoding='utf-8') as f:
                    json.dump(diverse_item, f, ensure_ascii=False)
                    f.write('\n')
    return len(chunk)

def process_and_save_diverse_answers():
    output_file = 'diverse_answers_ast_32.jsonl'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        pass

    with open('code_combined.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    manager = mp.Manager()
    lock = manager.Lock()

    num_processes = int(mp.cpu_count()/2)
    chunk_size = len(data) // num_processes
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    with mp.Pool(processes=num_processes) as pool:
        process_chunk_with_args = partial(process_chunk, output_file=output_file, lock=lock)
        processed_counts = list(tqdm(pool.imap(process_chunk_with_args, chunks), 
                                   total=len(chunks), 
                                   desc="Processing chunks"))
    
    total_processed = sum(processed_counts)
    print(f"Processed {total_processed} samples")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    process_and_save_diverse_answers()