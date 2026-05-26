"""AI 大模型 Agent 调度模块"""
import base64
import json
import re
from dataclasses import dataclass, field
import httpx
from config import AI_DEFAULT_TIMEOUT, AI_BATCH_SIZE, AI_BATCH_DELAY


@dataclass
class AIConfig:
    """AI 模型配置"""
    api_url: str
    api_key: str = ""
    model_name: str = "deepseek-chat"
    timeout: int = AI_DEFAULT_TIMEOUT


class AIAgent:
    """AI 大模型 Agent"""

    def __init__(self, config: AIConfig):
        self.config = config
        self._client = httpx.AsyncClient(timeout=config.timeout)

    async def score_image(self, image_path: str) -> dict:
        """对单张图片进行 AI 评分

        Returns:
            {"score": float, "details": {"quality": float, "lighting": float, "mood": float, "suitability": float}}
        """
        image_base64 = self._encode_image(image_path)

        prompt = """请对这张图片进行评分，用于朋友圈发布。评估以下维度（每个 0-100 分）：
1. quality - 画质清晰度
2. lighting - 光影效果
3. mood - 氛围感
4. suitability - 朋友圈适配度

请直接返回 JSON 格式，不要包含其他内容：
{"quality": 分数, "lighting": 分数, "mood": 分数, "suitability": 分数}"""

        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        # 构造消息内容（支持图片和纯文本模型）
        content = [{"type": "text", "text": prompt}]
        try:
            # 尝试添加图片（视觉模型支持）
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            })
        except Exception:
            pass

        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "user", "content": content}
            ],
            "max_tokens": 300,
        }

        response = await self._client.post(
            self.config.api_url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        # 解析响应内容
        content_text = data["choices"][0]["message"]["content"]
        details = self._parse_score_json(content_text)
        avg_score = sum(details.values()) / len(details)
        return {"score": round(avg_score, 1), "details": details}

    def _parse_score_json(self, text: str) -> dict:
        """从 AI 响应中解析评分 JSON（容错处理）"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试从 markdown 代码块中提取
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试从文本中提取第一个 JSON 对象
        match = re.search(r"\{[^{}]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从 AI 响应中解析评分: {text[:200]}")

    async def test_connection(self) -> bool:
        """测试模型服务连通性"""
        try:
            response = await self._client.get(
                self.config.api_url.replace("/chat/completions", "/models"),
                headers={"Authorization": f"Bearer {self.config.api_key}"} if self.config.api_key else {},
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def close(self):
        await self._client.aclose()


async def score_images_batch(agent: AIAgent, image_paths: list[str], on_progress=None) -> list[tuple[str, float]]:
    """批量 AI 评分（分片处理）"""
    import asyncio
    results = []
    total = len(image_paths)

    for i in range(0, total, AI_BATCH_SIZE):
        batch = image_paths[i:i + AI_BATCH_SIZE]
        batch_results = await asyncio.gather(
            *[agent.score_image(path) for path in batch],
            return_exceptions=True,
        )

        for path, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                results.append((path, 0.0))
            else:
                results.append((path, result["score"]))

        if on_progress:
            on_progress(min(i + AI_BATCH_SIZE, total), total)

        if i + AI_BATCH_SIZE < total:
            await asyncio.sleep(AI_BATCH_DELAY)

    return results
