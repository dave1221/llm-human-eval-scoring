#!/usr/bin/env python
# coding: utf-8
"""
Created on 2024/11/25 14:01
@author: Zhu Jiang
"""


# %%
from utils.llm_eval_utils import run_eval_custom
import os
from openai import OpenAI
from dotenv import load_dotenv
from utils.calculate_score import evaluate_functional_correctness
from utils.data_utils import HUMAN_EVAL

load_dotenv()


# %%
def entry_point(
    sample_file: str,
    k: str = "1,10",
    timeout: float = 3.0,
    problem_file: str = HUMAN_EVAL,
):
    """
    评估生成的样本代码的功能正确性，并将结果写入 "{sample_file}_results.jsonl.gz"。
    参数：
        sample_file (str): 包含生成的代码样本的文件路径（JSON Lines格式）。
        k (str): 用逗号分隔的整数列表，指定要计算的k值，默认为 "1,10,100"。
        timeout (float): 执行代码时的超时时间，单位为秒，默认值为3.0秒。
        problem_file (str): 包含问题描述的文件路径，默认使用 HUMAN_EVAL 常量。
    """
    k = list(map(int, k.split(",")))
    results = evaluate_functional_correctness(sample_file, k, timeout, problem_file)
    print(results)


# %%
if __name__ == '__main__':
    num_samples_per_task = 10
    model_name = os.getenv('DEEPSEEK_MODEL_NAME')
    out_path = f"results/eval_{model_name}_{num_samples_per_task}.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    client = OpenAI(
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        base_url=os.getenv('DEEPSEEK_BASE_URL')
    )

    # 运行评估
    run_eval_custom(
        client=client,
        model_name=model_name,
        num_samples_per_task=num_samples_per_task,
        out_path=out_path,
    )

    # 出分数
    entry_point(out_path)