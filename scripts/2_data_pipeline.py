# 文件路径: scripts/2_data_pipeline.py
import json
import os
import re
import sys
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from llm_utils import get_completion


# --- 工具函数 ---
def extract_code(text):
    if not text: return ""
    pattern = r"```python\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    pattern_simple = r"```\s*(.*?)\s*```"
    match_simple = re.search(pattern_simple, text, re.DOTALL)
    if match_simple: return match_simple.group(1).strip()
    return text.strip()


def verify_code_pair(bad_code, good_code, test_inputs):
    try:
        # 定义通用的 Header，预先导入常用库
        common_header = """
import math
import random
import json
import re
import datetime
import collections
from typing import List, Dict, Optional, Union, Any
"""
        loc_bad = {}
        loc_good = {}

        try:
            # 拼接 Header 和代码
            exec(common_header + "\n" + bad_code, {}, loc_bad)
            exec(common_header + "\n" + good_code, {}, loc_good)
        except Exception as e:
            # print(f"执行报错: {e}") # 调试时可以打开
            return False

        funcs_b = [v for k, v in loc_bad.items() if callable(v)]
        funcs_g = [v for k, v in loc_good.items() if callable(v)]

        if not funcs_b or not funcs_g: return False
        func_bad = funcs_b[-1]
        func_good = funcs_g[-1]

        for inputs in test_inputs:
            try:
                # 增强参数传递的兼容性
                # 如果输入是一个列表，且函数需要多个参数，尝试解包
                if isinstance(inputs, (list, tuple)):
                    try:
                        res_b = func_bad(*inputs)  # 尝试解包传参 func(a, b)
                        res_g = func_good(*inputs)
                    except TypeError:
                        res_b = func_bad(inputs)  # 失败则直接传 func([a, b])
                        res_g = func_good(inputs)
                else:
                    res_b = func_bad(inputs)
                    res_g = func_good(inputs)

                if res_b != res_g: return False
            except:
                return False
        return True
    except:
        return False


def process_single_topic(topic):
    # Step 1: 烂代码
    prompt_bad = f"请写一个Python函数，实现功能：{topic}。要求：变量名无意义(a,b,x)，无注释，逻辑啰嗦。仅输出代码块。"
    bad_code = extract_code(get_completion(prompt_bad))
    if not bad_code: return None

    # Step 2: 好代码
    prompt_good = f"你是一个Google高级软件工程师。重构以下代码：\n{bad_code}\n要求：Google Style，有意义变量名，加Docstring和Type Hints。仅输出代码块。"
    good_code = extract_code(get_completion(prompt_good))
    if not good_code: return None

    # Step 3: 测试用例
    prompt_test = f"针对功能：{topic}，生成3个测试输入列表。格式：[1, 5] 或 ['a', 'b']。只输出列表。"
    try:
        test_inputs = eval(extract_code(get_completion(prompt_test)))
        if not isinstance(test_inputs, list): test_inputs = []
    except:
        test_inputs = []
    if not test_inputs: return None

    # Step 4: 验证
    if verify_code_pair(bad_code, good_code, test_inputs):
        return {
            # 这里的 origin_topic 字段是为了让我们知道哪些跑过了
            "origin_topic": topic,
            "instruction": "请重构以下代码，使其符合 Google Style 规范并添加文档。",
            "input": bad_code,
            "output": good_code
        }
    return None


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    topics_path = os.path.join(base_dir, "dataset", "topics.json")
    output_path = os.path.join(base_dir, "dataset", "code_refactor.jsonl")

    # 1. 读取所有题目
    with open(topics_path, "r", encoding="utf-8") as f:
        all_topics = json.load(f)

    # 2. 读取已完成的题目 (断点续传核心逻辑)
    finished_topics = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "origin_topic" in data:
                        finished_topics.add(data["origin_topic"])
                except:
                    pass

    print(f"📊 总任务数: {len(all_topics)}")
    print(f"✅ 已完成: {len(finished_topics)}")

    # 3. 过滤出还需要跑的题目
    topics_to_run = [t for t in all_topics if t not in finished_topics]
    print(f"🚀 本次待运行: {len(topics_to_run)}")

    # 4. 开始运行
    if not topics_to_run:
        print("🎉 所有题目都已跑完！无需重复运行。")
    else:
        for topic in tqdm(topics_to_run):
            result = process_single_topic(topic)
            if result:
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")