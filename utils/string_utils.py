#!/usr/bin/env python
# coding: utf-8
"""
Created on 2024/11/24 17:19
@author: Zhu Jiang
"""


def fix_indents(text: str) -> str:
    """
    修正代码缩进，将制表符替换为四个空格。
    参数: text (str): 代码字符串。
    返回: str: 修正缩进后的代码字符串。
    """
    # 将所有的制表符('\t')替换为四个空格
    return text.replace("\t", "    ")


def process_completion(completion: str) -> str:
    """
    处理模型生成的代码completion字符串，清洗并提取有效的代码部分。
    参数：completion (str): 原始的代码completion字符串。
    返回：str: 处理后的代码字符串。
    """
    # 移除回车符号，统一换行符
    completion = completion.replace("\r", "")

    # 处理包含Markdown代码块的情况
    if "```python" in completion:
        # 找到"```python"的位置
        def_line = completion.index("```python")
        # 截取从"```python"开始的字符串
        completion = completion[def_line:].rstrip()
        # 移除第一个"```python"标记
        completion = completion.replace("```python", "", 1)
        # 尝试找到代码块的结束标记"```"
        try:
            next_line = completion.index("```")
            # 截取代码块内容
            completion = completion[:next_line].rstrip()
        except ValueError:
            # 如果未找到结束标记，可以选择打印警告信息或忽略
            print("警告：未找到代码块的结束标记```。")
            print(completion)
            print("================\n")

    # 处理包含主函数入口的情况，移除后续内容
    if '__name__ == "__main__"' in completion:
        # 找到主函数入口的位置
        next_line = completion.index('if __name__ == "__main__":')
        # 截取主函数入口之前的内容
        completion = completion[:next_line].rstrip()

    # 处理包含示例用法的情况，移除后续内容
    if "# Example usage" in completion:
        # 找到示例用法的位置
        next_line = completion.index("# Example usage")
        # 截取示例用法之前的内容
        completion = completion[:next_line].rstrip()

    return completion
