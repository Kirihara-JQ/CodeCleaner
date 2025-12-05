# 文件路径: scripts/1_gen_topics.py
import json
import sys
import os

# 把当前目录加入路径，确保能找到 llm_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from llm_utils import get_completion


def generate_topics():
    print("⏳ 正在请求 AI 生成题目...")
    prompt = """
    请生成 50 个 Python 编程练习题目。

    要求：
    1. 题目要具体，涵盖基础逻辑、字符串处理、列表/字典操作。
    2. 不要太难（避免复杂的动态规划），适合初学者练习。
    3. 格式严格要求：只输出一个 JSON 列表，不要 Markdown 标记，不要多余废话。

    示例：
    ["编写函数计算列表平均值", "反转字符串并大小写互换", "统计字典中值大于10的键"]
    """

    response = get_completion(prompt)

    if response:
        clean_text = response.replace("```json", "").replace("```", "").strip()
        try:
            topics = json.loads(clean_text)
            return topics
        except json.JSONDecodeError:
            print("⚠️ 解析 JSON 失败，AI 返回格式不对。")
    return []


if __name__ == "__main__":
    # 定义文件路径
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")
    save_path = os.path.join(dataset_dir, "topics.json")

    os.makedirs(dataset_dir, exist_ok=True)

    # --- 先读取旧数据 ---
    all_topics = []
    if os.path.exists(save_path):
        print(f"📂 发现已有题目文件，正在读取...")
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                all_topics = json.load(f)
            print(f"✅ 成功加载已有题目：{len(all_topics)} 个")
        except Exception as e:
            print(f"⚠️ 读取旧文件失败，将重新开始: {e}")
            all_topics = []
    else:
        print("📂 未发现旧文件，开始新创建...")

    initial_count = len(all_topics)

    # --- 继续生成 ---
    for i in range(100):
        print(f"--- 第 {i + 1} 轮追加生成 ---")
        new_topics = generate_topics()
        if new_topics:
            print(f"🌟 本轮生成了 {len(new_topics)} 个题目")
            all_topics.extend(new_topics)
        else:
            print("⚠️ 本轮生成失败，跳过")

    # --- 关键步骤：去重 ---
    unique_topics = list(set(all_topics))
    print(f"🧹 去重前: {len(all_topics)} -> 去重后: {len(unique_topics)}")

    # --- 保存回文件 ---
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(unique_topics, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 更新完成！总计保存 {len(unique_topics)} 个题目。")
    print(f"📈 本次新增: {len(unique_topics) - initial_count} 个")