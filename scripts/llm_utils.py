import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# 1. 加载 .env 文件中的环境变量
# 这一步会自动寻找根目录下的 .env 文件
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')

if load_dotenv(env_path):
    print("✅ 成功加载环境变量 (.env)")
else:
    print("⚠️ 未找到 .env 文件，请检查配置！")

# 2. 获取 Key 和 URL
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")

if not api_key:
    raise ValueError("❌ 错误：未在 .env 文件中找到 LLM_API_KEY")

# 3. 初始化客户端
client = OpenAI(api_key=api_key, base_url=base_url)


def get_completion(prompt, model="deepseek-chat", temperature=0.7):
    """
    封装好的调用函数
    :param prompt: 你发给 AI 的指令
    :param model: 模型名称 (DeepSeek V3 叫 deepseek-chat)
    :param temperature: 创造力 (0.0最严谨, 1.0最发散)
    :return: AI 的回复文本
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                # system 角色设定了 AI 的基调，这里设定为全能编程专家
                {"role": "system", "content": "你是一个精通Python的资深软件架构师，擅长代码重构与文档编写。"},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=4096  # 允许生成的最大长度
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        return None


# --- 单元测试 ---
# 只有直接运行这个文件时，下面的代码才会执行
if __name__ == "__main__":
    print("正在测试 API 连接...")
    test_prompt = "请用 Python 写一个 Hello World，并用一句话解释。"

    result = get_completion(test_prompt)

    if result:
        print("\n🎉 测试成功！模型回复如下：")
        print("-" * 30)
        print(result)
        print("-" * 30)
    else:
        print("\n😭 测试失败，请检查网络或 API Key。")