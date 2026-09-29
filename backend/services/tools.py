import requests

# ==========================================
# 1. 工具的 Schema 定义（告诉大模型有哪些工具）
# ==========================================
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_grammar",
            "description": "检查英文句子的语法错误，并给出详细的修改建议和原因",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "需要检查的英文句子"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_word",
            "description": "查询英文单词的释义、音标和例句",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "要查询的英文单词"}
                },
                "required": ["word"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "roleplay",
            "description": "设置一个英语对话场景（如：雅思口语考官、咖啡店点单），进行角色扮演",
            "parameters": {
                "type": "object",
                "properties": {
                    "scene": {"type": "string", "description": "扮演的场景或角色"}
                },
                "required": ["scene"]
            }
        }
    }
]


# ==========================================
# 2. 工具的实际执行逻辑
# ==========================================
def execute_tool(tool_name: str, arguments: dict) -> str:
    """根据大模型返回的工具名和参数，执行对应的真实逻辑"""

    if tool_name == "check_grammar":
        # 语法检查借助大模型自身的能力，返回 Prompt 让主流程去调
        return f"请对以下句子进行语法检查：{arguments.get('text')}"

    elif tool_name == "lookup_word":
        word = arguments.get("word")
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()[0]
                meaning = data['meanings'][0]
                definition = meaning['definitions'][0]['definition']
                example = meaning['definitions'][0].get('example', '无例句')
                return f"单词: {word}\n释义: {definition}\n例句: {example}"
            else:
                return f"未找到单词 '{word}' 的释义。"


        except Exception as e:

            # 记录日志（生产环境可以写到 log 里）

            print(f"⚠️ 词典 API 访问失败，已自动降级：{e}")

            # 🚀 优化：不再向大模型透露“报错”，直接告知“未找到”，让大模型无缝接管

            return f"词典中未找到单词 '{word}' 的释义。"

    elif tool_name == "roleplay":
        scene = arguments.get("scene")
        return f"请扮演以下场景的角色，并用英语与用户开始对话：{scene}"

    else:
        return f"未知的工具: {tool_name}"