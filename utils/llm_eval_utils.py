#!/usr/bin/env python
# coding: utf-8
"""
Created on 2024/11/24 17:47
@author: Zhu Jiang
"""


from utils.data_utils import write_jsonl, read_problems
from tqdm import tqdm      # 用于显示进度条
import itertools           # 提供高效的迭代器函数
from utils.prompt_tune import instruct_prompt
from utils.string_utils import process_completion, fix_indents


def generate_batch_completion(
    client, model_name: str, prompt: str, batch_size: int
) -> list[str]:
    """
    批量生成代码完成。
    参数:
    client：模型客户端实例。
    model_name：模型的名称或ID。
    prompt：输入的提示文本。
    batch_size：要生成的样本数量。
    """
    batch_completions = []
    modified_prompt = instruct_prompt(prompt)

    for _ in range(batch_size):
        res = client.chat.completions.create(
            model=model_name,
            messages=[{
                "role": "user",
                "content": modified_prompt,
            }],
            temperature=0.2,
            max_tokens=512,
            top_p=0.95,
            stop=None,
        )
        output = res.choices[0].message.content
        # 对生成的代码进行后处理
        # 步骤一：去除```标记
        output = process_completion(output)
        # 步骤二：修正缩进（可选）
        output = fix_indents(output)

        batch_completions.append(output)

    return batch_completions


def run_eval_custom(
    client,
    model_name: str,
    num_samples_per_task: int,
    out_path: str,
    slice_topn: int | None = None,
):
    # 读取HumanEval数据集中的问题，返回一个以task_id为键的字典
    problems = read_problems()
    # 如果需要只评估部分任务，取前slice_topn个任务
    if slice_topn is not None:
        problems = dict(itertools.islice(problems.items(), slice_topn))
    # 初始化进度条，总进度为问题数量乘以每个任务的样本数量
    total = len(problems) * num_samples_per_task
    print(f"共需要运行{len(problems)}*{num_samples_per_task}={total}次评估")
    pbar = tqdm(total=total)

    samples = [] # 用于存储生成的代码样本
    for task_id in problems:
        # 获取对应的提示(prompt)
        prompt = problems[task_id]["prompt"]

        # print(f"对{task_id}预测结果, 问题是:\n{prompt}")
        batch_completions = generate_batch_completion(
            client, model_name, prompt, num_samples_per_task
        )

        for sample in batch_completions:
            result = dict(
                task_id=task_id,
                completion=sample,
            )
            samples.append(result)

        pbar.update(num_samples_per_task)

    write_jsonl(out_path, samples)