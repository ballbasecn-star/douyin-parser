import os
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

def analyze_transcript(
    transcript: str, 
    api_key: Optional[str] = None,
    model: str = "Pro/deepseek-ai/DeepSeek-V3.2"
) -> Optional[dict]:
    """
    使用 SiliconFlow (Kimi-K2.5 等大模型) 对视频文案进行爆款拆解
    
    Args:
        transcript: 视频语音转录的文本
        api_key: SiliconFlow API Key。如果未提供，将尝试从环境变量中读取
        model: 使用的模型名称
        
    Returns:
        包含爆款拆解各维度的字典 (JSON格式解析出)
    """
    api_key = api_key or os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        logger.error("❌ 无法进行文案拆解: 缺少 SILICONFLOW_API_KEY 环境变量")
        return None

    logger.info(f"🧠 正在让 AI 深度拆解爆款文案... [模型: {model}]")

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 构建强大的 System Prompt
    system_prompt = """
你是一个资深短视频爆款文案拆解专家。你的任务是对用户提供的短视频口播文案进行深度拆解，提炼出其中的“爆款逻辑”。
你需要从以下 5 个核心维度进行拆解，并**严格按照要求输出一个合法的 JSON 格式**（不要有任何多余的 Markdown 标记或文字，直接返回大括号包含的 JSON 字符串）。

【需要提取的 5 个维度】
1. hook_text: 黄金前3秒（原句提取，即最开始的1-3句话）
2. hook_type: 钩子类型分类（例如：痛点切入、打破认知、制造悬念、利益直给、引发共鸣 等）
3. structure_type: 整体内容框架/行文逻辑（例如：SCQA模型、总分总盘点、反转式故事流、对比结构 等）
4. retention_points: 情绪留存点列表（提取文案中为了留住观众所说的转折句或高密度信息短句，最多3条，放在数组中）
5. scenario_expression: 场景化表达金句列表（提取把抽象功能具体化为“用户真实使用场景”的接地气话术，最多3条，放在数组中）
6. cta: 互动引导话术（提取结尾或中途呼吁点赞、评论、收藏和转发的原句，如果没有则为空字符串）

【返回 JSON 格式示例】
{
  "hook_text": "每天花两小时做PPT？试试这3个AI工具...",
  "hook_type": "痛点切入",
  "structure_type": "总分总盘点",
  "retention_points": ["但别急着去搜，重点是第三个..."],
  "scenario_expression": ["领导扔给你一份300页全英文财报，你直接丢给它..."],
  "cta": "怕下次找不到，赶紧先悄悄收藏起来"
}
"""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt.strip()
            },
            {
                "role": "user",
                "content": f"请对以下这段视频文案进行拆解：\n\n{transcript}"
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        result_json = response.json()
        
        # 尝试解析内容
        content = result_json["choices"][0]["message"]["content"]
        # 有时候模型还是会带 ```json \n ``` ，做一次简单的清洗
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        analysis_data = json.loads(content.strip())
        logger.info("✅ 文案拆解完成")
        return analysis_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 请求 AI 接口失败: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"响应内容: {e.response.text}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ 解析 AI 返回的 JSON 失败: {e}")
        logger.debug(f"AI 返回原文: {content}")
    except Exception as e:
        logger.error(f"❌ 文案拆解发生未知错误: {e}")

    return None
