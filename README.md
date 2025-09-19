# PixAI 项目
文章使用的AI模型为PixAI(https://www.modelscope.cn/models/deepghs/pixai-tagger-v0.9-onnx)，该模型在本项目中基于ONNX Runtime GPU版本运行，支持CUDA加速。
## 项目概述
本项目包含三个主要模块：
- **web_app.py**：基于 Flask 的图片查询与浏览应用，可根据 tag 进行模糊或组合搜索。
- **generate_top_tags.py**：根据图片 tags 生成 top tags 列表，用于在 Web 应用中提供搜索建议。
- **folder_tagger.py**：批量提取图片 tags，其中支持提取 sexual 标签，并在终端中显示进度条。

## 环境配置
- Python 版本：3.10
- 环境依赖：
  - Flask 版本：3.1.2
  - pandas 版本：2.3.2
  - huggingface-hub 版本：0.34.4
  - onnxruntime-gpu 版本：1.22.0
  - torch 版本：2.8.0+cu126
  - torchvision 版本：0.23.0+cu126
## 安装依赖
```bash
# 先确保安装了 CUDA 12.x和对应的cudnn版本
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
# 安装模型依赖
pip install onnxruntime-gpu
pip install dghs-imgutils >= 0.19.0
# 安装其他依赖
pip install flask
```

## 使用说明

### 1. 将图片文件夹放入figure目录中，支持多个文件夹
### 2. 运行main.py
```bash
python main.py
```
### 3. 访问 Web 应用
在浏览器中访问 `http://127.0.0.1:5000` 进行查询。


## 项目结构
- `web_app.py`：Web 图片查询与浏览应用  
- `generate_top_tags.py`：根据图片 tags 生成 top tags 列表  
- `folder_tagger.py`：批量图片 tag 提取脚本  
- `README.md`：项目说明文件  
- `figure/`：存放所有图片及子目录

## 注意事项
- 对于搜索关键词 **ass**，使用 REGEXP 进行匹配，并排除包含 "glasses" 的记录。还会存在更多类似的关键词但是懒得改了。
- get_tags函数存在full变量，默认值为False，当full为True时，会重新提取所有图片的tags适用于更改了SEXUAL_ROOTS后重新进行识别。若未更改而只对图片进行了增删则无需设置为True。