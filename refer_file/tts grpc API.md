


# 2. **TTS GRPC 流式API**



## **概述**



这是一个基于 Triton Server 的 文本转语音(TTS)流式接口，支持中英文混合语音合成，并提供实时流式音频输出。



## **服务信息**



* **模型名称**: cloudsway\_tts

* **协议**: GRPC

* **服务端点**: 116.148.216.100

* **支持功能**: 流式音频合成、多语言支持、声音克隆



## **接口规范**



### **输入参数**





### **输出参数**



| 参数名称         | 数据类型  | 描述                     |
| ------------ | ----- | ---------------------- |
| `wav_output` | BYTES | 流式音频数据块，以 `%END%` 标记结束 |



### **语言代码说明**



| 代码       | 描述 |
| -------- | -- |
| `zh` | 中文 |
| `en`     | 英文 |



## **使用示例**



### **Python 客户端示例**



```python
import tritonclient.grpc as grpcclient
import numpy as np
from functools import partial

def callback(user_data, result, error):
    if error:
        user_data._completed_requests.put(error)
    else:
        user_data._completed_requests.put(result)

# 创建输入数据
inputs = []

# 参考音频路径
ref_audio = grpcclient.InferInput("voice_id", [1], "BYTES")
ref_audio.set_data_from_numpy(np.array(["reference"], dtype=np.object_))
inputs.append(ref_audio)

# 文本
prompt_text = grpcclient.InferInput("text", [1], "BYTES")
prompt_text.set_data_from_numpy(np.array(["这是文本"], dtype=np.object_))
inputs.append(prompt_text)

# 其他参数...
# (参照完整示例代码)

# 创建客户端连接
with grpcclient.InferenceServerClient(url="103.216.252.18:8001") as client:
    # 启动流式连接
    client.start_stream(callback=partial(callback, user_data))
    
    # 发送推理请求
    client.async_stream_infer(
        model_name="cloudsway_tts",
        inputs=inputs,
        outputs=[grpcclient.InferRequestedOutput("wav_output")]
    )
    
    # 处理流式响应
    with open("output.wav", "wb") as f:
        while True:
            result = user_data._completed_requests.get()
            audio_chunk = result.as_numpy("wav_output")[0]
            if audio_chunk == b'%END%':
                break
            f.write(audio_chunk)
```



### **JSON 输入示例**



```json
{
  "inputs": [
    {
      "name": "voice_id",
      "shape": [1],
      "datatype": "BYTES",
      "data": ["infer_2_moan_1"]
    },
    {
      "name": "language",
      "shape": [1],
      "datatype": "BYTES",
      "data": ["en"]
    },
    {
      "name": "text",
      "shape": [1],
      "datatype": "BYTES",
      "data": ["Hello, this is a test of the streaming TTS API. This is a longer text to test streaming functionality."]
    },
    {
      "name": "sample_rate",
      "shape": [1],
      "datatype": "INT32",
      "data": [16000]
    },
    {
      "name": "api_key",
      "shape": [1],
      "datatype": "BYTES",
      "data": [""]
    }
  ]
}
```





### **音频质量**

* **采样率**: 16kHz (可配置)

* **格式**: WAV

* **声道**: 单声道

* **位深**: 16位



## **错误处理**



### **常见错误代码**



| 错误类型 | 描述        | 解决方案         |
| ---- | --------- | ------------ |
| 连接超时 | 服务器无响应    | 检查网络连接和服务器状态 |
| 参数错误 | 输入参数格式不正确 | 验证参数类型和格式    |
| 模型错误 | 模型推理失败    | 检查参考音频和文本内容  |
| 流中断  | 流式连接中断    | 重新建立连接并重试    |



### **异常处理示例**



```python
try:
    # 推理代码
    pass
except InferenceServerException as e:
    print(f"推理服务异常: {e}")
except queue.Empty:
    print("请求超时")
except Exception as e:
    print(f"其他异常: {e}")
```





## **依赖要求**



```plain&#x20;text
tritonclient[grpc]>=2.20.0
numpy>=1.21.0
```