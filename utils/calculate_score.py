#!/usr/bin/env python
# coding: utf-8
"""
Created on 2024/11/25 10:36
@author: Zhu Jiang
"""

from typing import List, Union  # 用于类型提示
import numpy as np  # 数值计算库，用于数组和矩阵运算
import itertools  # 提供高效的迭代器函数
from collections import defaultdict, Counter  # defaultdict用于创建带有默认值的字典，Counter用于计数
import tqdm  # 用于显示进度条

from utils.data_utils import HUMAN_EVAL, read_problems, stream_jsonl, write_jsonl
from utils.execution_completion import check_correctness


def estimate_pass_at_k(
    num_samples: Union[int, List[int], np.ndarray],
    num_correct: Union[List[int], np.ndarray],
    k: int,
) -> np.ndarray:
    """
    估计每个问题的 pass@k 值，并以数组形式返回。
    参数：
        num_samples：一个整数、整数列表或 numpy 数组，表示每个问题的样本数量。
        num_correct：整数列表或numpy数组，表示每个问题的正确样本数量。
        k：整数，表示 k 的值，即计算 pass@k 指标中的 k。
    返回值：numpy 数组，包含每个问题的 pass@k 估计值。
    """
    def estimator(n: int, c: int, k: int) -> float:
        """
        计算单个问题的 pass@k 值，使用组合数学公式。
        Calculates 1 - comb(n - c, k) / comb(n, k).
        """
        if n - c < k:
            # 如果错误的样本数小于 k，则 pass@k 为 1.0
            return 1.0
        # 使用组合数的等价形式计算 pass@k，避免计算大数阶乘
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

    if isinstance(num_samples, int):
        # 如果 num_samples 是整数，表示所有问题的样本数量相同
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        # 检查 num_samples 和 num_correct 的长度是否一致
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    # 对每个问题计算 pass@k，返回 numpy 数组
    return np.array(
        [estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)]
    )


def evaluate_functional_correctness(
    sample_file: str,
    k: List[int] | None = None,
    timeout: float = 3.0,
    problem_file: str = HUMAN_EVAL,
):
    """
    评估生成的样本代码的功能正确性，并将结果写入 "{sample_file}_results.jsonl.gz"
    参数：
        sample_file：字符串，模型生成的样本文件的路径（JSON Lines 格式）。
        k：整数列表，指定要计算的 k 值列表，默认是 [1, 10, 100]。
        n_workers：整数，线程池的最大工作线程数，默认是4。
        timeout：浮点数，执行代码时的超时时间，默认是 3.0 秒。
        problem_file：字符串，包含问题描述的文件路径，默认是 HUMAN_EVAL。
    """
    # 读取原始评测数据human eval数据
    if k is None:
        k = [1, 10]
    problems = read_problems(problem_file)

    # 初始化
    completion_id = Counter()
    n_samples = 0
    results = defaultdict(list)

    print("读取生成的样本，开始评估...")
    for sample in tqdm.tqdm(stream_jsonl(sample_file)):
        # 提取 task_id 和生成的代码 completion
        task_id = sample["task_id"]
        completion = sample["completion"]
        # 调用 check_correctness 函数，检查代码的功能正确性
        # 其中completion_id[task_id]是每个问题的计数表示id
        result = check_correctness(problems[task_id], completion, timeout, completion_id[task_id])
        # 将结果添加到 results 字典中，按 task_id 组织，存储为列表，元素是 (completion_id, result) 的元组
        results[task_id].append((result["completion_id"], result))
        # 更新计数器
        completion_id[task_id] += 1
        n_samples += 1

    # 断言：确保所有问题都被尝试过
    assert len(completion_id) == len(problems), "存在没有评估的问题, 评估未完成。。。"

    # 计算 pass@k 指标
    total, correct = [], []
    # 遍历 results 中的每个问题的结果列表
    for result_list in results.values():
        # 按照 completion_id 排序
        result_list.sort()
        # 提取 passed 列表，表示每个样本是否通过测试
        passed = [r[1]["passed"] for r in result_list]
        # 总测试数
        total.append(len(passed))
        # 总正确数
        correct.append(sum(passed))
    total = np.array(total)
    correct = np.array(correct)

    ks = k
    # 计算每个问题的 pass@k，取平均值作为总体 pass@k
    # 只有当所有问题的 total 样本数大于等于 k 时，才计算对应的 pass@k
    pass_at_k = {
        f"pass@{k}": estimate_pass_at_k(total, correct, k).mean()
        for k in ks if (total >= k).all()
    }

    # 保存结果
    def combine_results():
        """
        组合原始样本和评估结果
        """
        for sample in stream_jsonl(sample_file):
            task_id = sample["task_id"]
            result = results[task_id].pop(0)
            sample["result"] = result[1]["result"]
            sample["passed"] = result[1]["passed"]
            yield sample

    # 构造输出文件路径，在原文件名后添加 _eval_results.jsonl
    out_file = sample_file + "_eval_results.jsonl"
    print(f"将结果写入文件: {out_file}...")
    write_jsonl(out_file, tqdm.tqdm(combine_results(), total=n_samples))

    return pass_at_k