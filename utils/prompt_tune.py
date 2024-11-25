#!/usr/bin/env python
# coding: utf-8
"""
Created on 2024/11/24 17:16
@author: Zhu Jiang
"""


def instruct_prompt(prompt: str) -> str:
    new_prompt = f'''
    # Below is an instruction that describes a task. Write a response that appropriately completes the request.
    
    ### Instruction:
    Please complete the implementation of the following function **by providing only the code inside the function body**. Do not include the function signature, docstring, tests, or any explanations.
    
    **Ensure that your code is properly indented to fit within the function body. All code lines should be indented with at least 4 spaces.**
    
    {prompt}

    ### Response:
    '''
    return new_prompt
