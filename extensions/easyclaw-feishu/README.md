# EasyClaw + Feishu Extension

**三个 Skill，让你的 LLM Wiki 能从更多来源自动入库。**

这个扩展包是为 [EasyClaw](https://easyclaw.com) + 飞书用户设计的。如果你不用 EasyClaw 和飞书，这些 Skill 对你没用——但你可以参考代码实现类似功能。

## 🎯 这三个 Skill 能做什么？

| Skill | 输入 | 输出 |
|-------|------|------|
| **wiki-video-ingest** | 飞书群里的视频消息 | 转录文本 → `wiki/raw/video/` |
| **wiki-web-ingest** | 任意网页 URL | Markdown 正文 → `wiki/raw/` |
| **wiki-feishu-transfer** | 飞书群里的文件 | 转存到飞书云盘（归档） |

## 📦 前置条件

1. **EasyClaw** 已安装并配置飞书频道
2. **Python 3** + `requests` 库
3. **ffmpeg**（仅 wiki-video-ingest 需要）
4. 飞书 App 开通以下权限：
   - `im:message:readonly`（下载消息文件）
   - `drive:drive`（上传云盘）

## 🔧 安装

把整个 `easyclaw-feishu/` 目录复制到你的 EasyClaw skills 目录：

```bash
# Windows
xcopy /E /I extensions\easyclaw-feishu %USERPROFILE%\.easyclaw\skills\

# macOS/Linux
cp -r extensions/easyclaw-feishu ~/.easyclaw/skills/
```

## ⚙️ 配置

### wiki-video-ingest

编辑 `wiki_video_ingest.py` 中的常量（如需）：

```python
FFMPEG_PATH = r"C:\tools\ffmpeg\bin\ffmpeg.exe"  # 改成你的 ffmpeg 路径
TEMP_DIR = r"C:\temp\wiki_video_temp"  # 临时文件目录
```

### wiki-feishu-transfer

编辑 `wiki_feishu_transfer.py` 或在调用时指定：

```python
DEFAULT_DRIVE_FOLDER = "你的云盘文件夹token"  # 从飞书云盘 URL 获取
```

或者调用时传参：
```bash
python wiki_feishu_transfer.py <message_id> <file_key> --filename "xxx.mp4" --drive-folder "你的folder_token"
```

## 📖 使用示例

### 转录视频

```bash
python wiki_video_ingest.py om_abc123 file_v3_xxx \
  --title "Karpathy 谈 LLM" \
  --platform "YouTube" \
  --output-dir "/path/to/wiki/raw/video"
```

### 抓取网页

```bash
python wiki_web_ingest.py "https://mp.weixin.qq.com/s/xxx" \
  --output-dir "/path/to/wiki/raw/wechat"
```

### 转存文件到云盘

```bash
python wiki_feishu_transfer.py om_abc123 file_v3_xxx \
  --filename "会议录像.mp4"
```

## 🔗 典型工作流

1. 用户在飞书群发视频："wiki 视频：Karpathy 最新演讲"
2. Agent 调用 `wiki-video-ingest` 转录 → 存入 `wiki/raw/video/`
3. Agent 调用 `wiki-feishu-transfer` 归档原视频 → 存入飞书云盘
4. Agent 从转录文本提炼知识 → 更新 wiki 页面

## 📝 输出格式

所有 Skill 输出 JSON 到 stdout：

```json
{
  "status": "success",
  "transcript_path": "/path/to/file.md",
  "word_count": 3500,
  ...
}
```

错误时：
```json
{
  "status": "error",
  "error": "错误描述"
}
```

## 🐛 已知问题

1. **微信公众号反爬**：部分文章需要 JS 渲染，web-ingest 会返回错误提示，改用 browser-tool 抓取
2. **大视频转录慢**：1 小时视频约需 5-10 分钟转录
3. **飞书域名切换**：国际版/国内版自动 fallback，偶尔需要重试

## 📜 License

MIT — 同主仓库
