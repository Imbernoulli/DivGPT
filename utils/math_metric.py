import torch
from vllm import LLM, SamplingParams
import multiprocessing as mp
from typing import List
import os
import json
from datetime import datetime
import re
from math import isclose
import sympy as sp
from tqdm import tqdm
import random

from sympy import simplify, N
from sympy.parsing.sympy_parser import parse_expr
from sympy.parsing.latex import parse_latex
from latex2sympy import latex2sympy

from transformers import AutoTokenizer

from symeval import EvaluatorMathBatch

evaluator = EvaluatorMathBatch()


def extract_answer(pred_str, use_last_number=True):
    """从推理过程或模型输出中提取最后的答案。"""
    if "boxed" in pred_str:
        ans = pred_str.split("boxed")[-1]
        if len(ans) == 0:
            return ""
        elif ans[0] == "{":
            stack = 1
            a = ""
            for c in ans[1:]:
                if c == "{":
                    stack += 1
                    a += c
                elif c == "}":
                    stack -= 1
                    if stack == 0:
                        break
                    a += c
                else:
                    a += c
        else:
            a = ans.split("$")[0].strip()
        pred = a
    elif "final answer is $" in pred_str and "$. I hope" in pred_str:
        tmp = pred_str.split("final answer is $", 1)[1]
        pred = tmp.split("$. I hope", 1)[0].strip()
    else:
        if use_last_number:
            pattern = "-?\d*\.?\d+"
            pred = re.findall(pattern, pred_str.replace(",", ""))
            if len(pred) >= 1:
                pred = pred[-1]  # 提取最后的一个数字
            else:
                pred = ""
        else:
            pred = ""
    
    return pred.strip()

def parse_digits(num):
    """移除逗号，解析成浮点数"""
    num = re.sub(",", "", str(num))
    try:
        return float(num)
    except ValueError:
        if num.endswith("%"):
            num = num[:-1]
            try:
                return float(num) / 64
            except ValueError:
                pass
    return None

def numeric_equal(prediction: float, reference: float) -> bool:
    """比较两个浮点数是否在允许误差范围内相等"""
    return isclose(prediction, reference, rel_tol=1e-4)


def symbolic_equal(a, b):
    def _parse(s):
        for f in [parse_latex, parse_expr, latex2sympy]:
            try:
                return f(s.replace("\\\\", "\\"))
            except:
                try:
                    return f(s)
                except:
                    pass
        return s

    a = _parse(a)
    b = _parse(b)

    # direct equal
    try:
        if str(a) == str(b) or a == b:
            return True
    except:
        pass

    # simplify equal
    try:
        if a.equals(b) or simplify(a - b) == 0:
            return True
    except:
        pass

    # equation equal
    try:
        if (abs(a.lhs - a.rhs)).equals(abs(b.lhs - b.rhs)):
            return True
    except:
        pass

    try:
        if numeric_equal(float(N(a)), float(N(b))):
            return True
    except:
        pass

    # matrix
    try:
        # if a and b are matrix
        if a.shape == b.shape:
            _a = a.applyfunc(lambda x: round(x, 3))
            _b = b.applyfunc(lambda x: round(x, 3))
            if _a.equals(_b):
                return True
    except:
        pass

    return False


def math_equal(prediction: str, reference: str, include_percentage: bool=True) -> bool:
    """
    用于比较预测值和参考值是否相同，先尝试数值相等，再尝试符号相等。
    """
    # 1. 数值相等比较
    try:
        if evaluator.eq(prediction, reference):
            return True
    except:
        pass
    
    if parse_digits(prediction) is not None and parse_digits(reference) is not None:
        prediction_num = parse_digits(prediction)
        reference_num = parse_digits(reference)
        # 如果允许百分比，考虑转换百分比进行比较
        if include_percentage:
            gt_result = [reference_num / 64, reference_num, reference_num * 64]
        else:
            gt_result = [reference_num]
        
        for item in gt_result:
            if numeric_equal(prediction_num, item):
                return True

    # 2. 符号相等比较
    if symbolic_equal(prediction, reference):
        return True

    return False