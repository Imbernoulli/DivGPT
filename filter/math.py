import json
import numpy as np
import re
from collections import Counter
from itertools import combinations
from tqdm import tqdm
import multiprocessing as mp
from functools import partial

from utils import extract_answer, math_equal

def get_ngrams(text, n):
    """获取文本的n-gram"""
    tokens = text.split()
    return set(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

def compute_similarity_matrix(texts, n=3):
    """计算文本间的n-gram相似度矩阵"""
    num_texts = len(texts)
    similarity_matrix = np.zeros((num_texts, num_texts))
    
    ngrams_list = [get_ngrams(text, n) for text in texts]
    for i, j in combinations(range(num_texts), 2):
        intersection = len(ngrams_list[i] & ngrams_list[j])
        union = len(ngrams_list[i] | ngrams_list[j])
        sim = intersection / union if union != 0 else 0
        similarity_matrix[i,j] = similarity_matrix[j,i] = sim
    
    np.fill_diagonal(similarity_matrix, 1)
    return similarity_matrix

def select_diverse_responses(responses, n=32, ngram_size=3):
    """选择最不相似的n个答案"""
    if len(responses) <= n:
        return responses
    
    similarity_matrix = compute_similarity_matrix(responses, n=ngram_size)
    
    selected_indices = [0] 
    while len(selected_indices) < n:
        remaining_indices = list(set(range(len(responses))) - set(selected_indices))
        max_similarities = []
        
        for idx in remaining_indices:
            max_sim = max(similarity_matrix[idx][selected_indices])
            max_similarities.append((max_sim, idx))
        
        _, next_idx = min(max_similarities)
        selected_indices.append(next_idx)
    
    return [responses[i] for i in selected_indices]

def process_chunk(chunk, output_file, lock):
    """处理数据块并实时写入结果的函数"""
    for item in tqdm(chunk):
        item['resps'] = [i for i in item['resps'] if math_equal(extract_answer(i), item['gt_ans'])]
        if len(item['resps']) >= 1:
            diverse_responses = select_diverse_responses(item['resps'], n=32)
            diverse_item = {
                'query': item['query'],
                'gt_ans': item['gt_ans'],
                'diverse_responses': diverse_responses
            }
            with lock:
                with open(output_file, 'a', encoding='utf-8') as f:
                    json.dump(diverse_item, f, ensure_ascii=False)
                    f.write('\n')
    return len(chunk)

def process_and_save_diverse_answers():
    output_file = 'diverse_answers_32.jsonl'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        pass

    with open('math_combined.json', 'r', encoding='utf-8') as f:
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