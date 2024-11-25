#!/usr/bin/env python
# coding: utf-8
"""
Created on 2024/11/25 10:26
@author: Zhu Jiang
"""


import subprocess
import sys
import tempfile
import os
from typing import Optional, Dict  # 用于类型提示


def execute_code_with_timeout(code_str: str, timeout: float = 3., temp_dir: str | None = None):
    """
    执行给定的代码字符串，在单独的进程中运行，并限制执行时间。
    - 将给定的代码字符串写入一个临时的 Python 脚本文件。
    - 使用 subprocess 模块在单独的进程中执行该脚本。
    - 使用 communicate(timeout=timeout) 方法设置超时时间。
    - 捕获执行结果、标准输出、标准错误和超时异常。
    该方法适用于 Windows 系统，无需使用 multiprocessing 模块和 if __name__ == '__main__' 块。
    该方法也适用于类 Unix 系统（如 Linux、macOS）。
    参数：
        code_str (str): 要执行的代码字符串。
        timeout (float): 超时时间（秒），默认为 3 秒。
        temp_dir (str): 临时文件的存储目录，默认为当前虚拟环境的 tmp 文件夹。
    返回：
        result：包含执行结果的列表，可能的值为：
            'passed'：执行成功，无错误。
            'timed out'：执行超时。
            'failed: {错误信息}'：执行失败，包含错误信息。
    示例：
        result = execute_code_with_timeout('print("Hello, World!")', timeout=3)
    """
    result = []
    tmp_file_path = None  # 初始化变量，以便在 finally 块中使用

    try:
        if temp_dir is None:
            # 获取当前虚拟环境的目录
            # 返回当前 Python 解释器的安装路径，通常在虚拟环境中，它指向虚拟环境的根目录。
            venv_dir = sys.prefix
            temp_dir = os.path.join(venv_dir, 'tmp')
        # 确保临时目录存在, 如果目录已存在，不会引发异常。
        os.makedirs(temp_dir, exist_ok=True)

        # 创建一个临时文件，后缀为 .py; 将代码写入临时文件
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py', dir=temp_dir) as tmp_file:
            tmp_file.write(code_str)
            tmp_file_path = tmp_file.name

        # 使用当前的 Python 解释器执行临时脚本文件。重定向标准输出和标准错误，便于捕获输出和错误信息。
        process = subprocess.Popen(
            [sys.executable, tmp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            # 使用 communicate 方法等待进程完成，或在超时时间后抛出 TimeoutExpired 异常。
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode == 0:
                # 执行成功, 将 'passed' 添加到结果列表。
                result.append('passed')
                # 如果有标准输出，打印输出内容。
                if stdout.strip():
                    print(stdout.strip())
            else:
                # 如果返回码不为 0，表示执行失败。捕获标准错误信息，添加到结果列表。
                error_info = f'failed: {stderr.strip()}'
                result.append(error_info)
        except subprocess.TimeoutExpired:
            # 当发生超时异常时，终止进程并等待进程结束。
            process.kill()
            process.wait()
            # 将 'timed out' 添加到结果列表。
            result.append('timed out')
    except Exception as e:
        # 捕获其他异常
        result.append(f'failed: {e}')
    finally:
        # 清理临时文件
        if tmp_file_path and os.path.exists(tmp_file_path):
            # 尝试删除临时文件，防止占用磁盘空间。
            try:
                os.remove(tmp_file_path)
            except OSError:
                pass

    return result


def check_correctness(problem: Dict, completion: str, timeout: float,
                      completion_id: Optional[int] = None) -> Dict:
    """
    通过运行问题提供的测试套件，评估生成的代码（completion）的功能正确性。
    函数目的：评估生成的代码 completion 是否正确，即是否通过了问题 problem 中提供的测试套件。
    参数：
        problem (Dict): 包含问题描述、测试用例等信息的字典。
        completion (str): 生成的代码字符串，需要被评估。
        timeout (float): 代码执行的超时时间，单位为秒。
        completion_id (Optional[int]): 可选的完成ID
    返回：
        Dict: 包含评估结果的字典，包括任务ID、是否通过测试、结果描述和完成ID。
    """
    # 构建待执行的完整代码字符串，包括提示、生成的代码和测试用例。组合成一个完整的代码。
    check_program = (
            problem["prompt"] + completion + "\n" +
            problem["test"] + "\n" +
            f"check({problem['entry_point']})"
    )
    # 执行给定的代码字符串，在单独的进程中运行，并限制执行时间。
    execution_result = execute_code_with_timeout(check_program, timeout=timeout)

    return {
        "task_id": problem["task_id"],
        "passed": execution_result[0] == "passed", # 布尔值，指示是否通过测试，即结果是否为 "passed"
        "result": execution_result[0], # 字符串，记录执行结果（"passed"、"timed out" 或包含错误信息的字符串）。
        "completion_id": completion_id, # 生成的代码的ID（如果提供）。
    }