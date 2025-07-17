from abc import ABC, abstractmethod
import openai
import logging
import requests
import yaml
import os
import json


logger = logging.getLogger(__name__)


class LLM(ABC):
    @abstractmethod
    def response(self, dialogue):
        pass


class OpenAILLM(LLM):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        self.base_url = config.get("url")
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    def response(self, dialogue):
        try:
            responses = self.client.chat.completions.create(  #) ChatCompletion.create(
                model=self.model_name,
                messages=dialogue,
                stream=True
            )
            for chunk in responses:
                yield chunk.choices[0].delta.content
                #yield chunk.choices[0].delta.get("content", "")
        except Exception as e:
            logger.error(f"Error in response generation: {e}")

    def response_call(self, dialogue, functions_call):
        try:
            responses = self.client.chat.completions.create(  #) ChatCompletion.create(
                model=self.model_name,
                messages=dialogue,
                stream=True,
                tools=functions_call
            )
            #print(responses)
            for chunk in responses:
                yield chunk.choices[0].delta.content, chunk.choices[0].delta.tool_calls
                #yield chunk.choices[0].delta.get("content", "")
        except Exception as e:
            logger.error(f"Error in response generation: {e}")


class BaiDuLLM(LLM):
    def __init__(self, config):
        self.api_url = config.get("api_url")
        self.api_key = config.get("api_key")
        self.app_id = config.get("app_id", "")
        self.model_name = config.get("model_name", "c0jkrl3v_dt24b")
        self.temperature = config.get("temperature", 1)
        self.top_p = config.get("top_p", 0.5)
        self.penalty_score = config.get("penalty_score", 1)
        self.safety = config.get("safety", {"input_level": "none"})

    def response(self, dialogue):
        headers = {
            'Content-Type': 'application/json',
            'appid': self.app_id,
            'Authorization': f'Bearer {self.api_key}'
        }
        payload = {
            "model": self.model_name,
            "messages": dialogue,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "penalty_score": self.penalty_score,
            "safety": self.safety
        }
        try:
            resp = requests.post(self.api_url, headers=headers, 
                               data=json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            resp_json = resp.json()
            if 'choices' in resp_json and len(resp_json['choices']) > 0:
                model_reply = resp_json['choices'][0]['message']['content']
                yield model_reply
            else:
                logger.error(f"BaiDuLLM: No valid response: {resp_json}")
                yield "Error: No valid response from API."
        except Exception as e:
            logger.error(f"BaiDuLLM Error: {e}")
            yield f"Error: {e}"

    def response_call(self, dialogue, functions_call):
        """
        百度千帆大模型的函数调用实现
        目前为基础实现，可根据百度API文档进一步扩展
        """
        headers = {
            'Content-Type': 'application/json',
            'appid': self.app_id,
            'Authorization': f'Bearer {self.api_key}'
        }
        payload = {
            "model": self.model_name,
            "messages": dialogue,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "penalty_score": self.penalty_score,
            "safety": self.safety
        }
        
        # 如果百度千帆支持函数调用，可以在这里添加 tools 参数
        # 目前大部分百度模型还不支持函数调用，所以先用基础实现
        if functions_call:
            # payload["tools"] = functions_call  # 取消注释如果百度API支持
            pass
        
        try:
            resp = requests.post(self.api_url, headers=headers, 
                               data=json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            resp_json = resp.json()
            if 'choices' in resp_json and len(resp_json['choices']) > 0:
                model_reply = resp_json['choices'][0]['message']['content']
                # 返回 (content, tool_calls) 格式，与 OpenAILLM 保持一致
                yield model_reply, None
            else:
                logger.error(f"BaiDuLLM: No valid response: {resp_json}")
                yield "Error: No valid response from API.", None
        except Exception as e:
            logger.error(f"BaiDuLLM Error: {e}")
            yield f"Error: {e}", None


def create_instance(class_name, *args, **kwargs):
    # 获取类对象
    cls = globals().get(class_name)
    if cls:
        # 创建并返回实例
        return cls(*args, **kwargs)
    else:
        raise ValueError(f"Class {class_name} not found")


def get_prompt(key):
    prompts_path = os.path.join(os.path.dirname(__file__), "prompts.yaml")
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    return prompts.get(key, "")


if __name__ == "__main__":
    # 用法示例
    CHARACTER_PROMPT = get_prompt("character_prompt")
    deepseek = create_instance("DeepSeekLLM", api_key="your_api_key", base_url="your_base_url")
    dialogue = [{"role": "user", "content": CHARACTER_PROMPT}]
    # 打印逐步生成的响应内容
    for chunk in deepseek.response(dialogue):
        print(chunk)
