# astrbot_plugin_ayling_meme

## 插件作用

这是一个支持 LLM 多标签语义选择表情包的 AstrBot QQ 表情包插件，而不是传统关键词触发。

让角色扮演 Bot 通过 `<meme:shy,tease>` 输出多标签表情意图，插件自动匹配图床表情包并发送。
适用于陪伴、人格化、QQ 拟真聊天场景。

当 LLM 在回复文本中输出 `<meme:...>` 标记时，插件会在发送消息前拦截最终结果：

- 从文本中移除所有 `<meme:...>` 标记
- 保留剩余文本正常发送
- 使用第一个标记里的标签，从 `meme_data.json` 中选择一张 URL 图片
- 在消息链末尾追加该图片

示例：

```text
才没有等你消息…<meme:shy,tease>
```

最终效果：

- 发送文本：`才没有等你消息…`
- 额外发送一张匹配 `shy + tease` 的表情包图片

## 核心卖点

- 支持 LLM 输出多标签语义标记，而不是单一关键词触发
- 可让模型表达更细腻的情绪组合，例如 `shy + tease`、`sleepy + care`
- 表情图来自图床 URL，不依赖本地文件和上传逻辑
- 自动清理控制标签，最终发送内容更自然
- 结构轻量，适合低内存云服务器

如果一条回复里有多个 `<meme:...>`：

- 只使用第一个标记作为选图依据
- 但会移除文本中的所有标记

如果 `main.py` 顶部的 `ENABLE_MEME = False`：

- 仍然会清理标记
- 但不会发送图片

## 安装路径

将整个插件目录放到 AstrBot 插件目录中：

```text
AstrBot/data/plugins/astrbot_plugin_ayling_meme/
```

目录结构如下：

```text
astrbot_plugin_ayling_meme/
  metadata.yaml
  main.py
  meme_data.json
  README.md
```

## meme_data.json 示例

`meme_data.json` 使用“每张图带 tags”的结构：

```json
[
  {
    "url": "https://example.com/001.gif",
    "tags": ["shy", "tease", "soft"],
    "weight": 1
  },
  {
    "url": "https://example.com/002.gif",
    "tags": ["speechless", "tease"],
    "weight": 2
  },
  {
    "url": "https://example.com/003.png",
    "tags": ["sleepy", "care"],
    "weight": 1
  }
]
```

字段说明：

- `url`：必须以 `http` 或 `https` 开头
- `tags`：字符串数组
- `weight`：可选，默认为 `1`，用于加权随机

## LLM Prompt 中如何使用

你可以在 AstrBot 的人格提示词或系统提示词中告诉模型：

```text
当语气适合发送表情包时，在回复结尾附加一个表情标记，格式为 <meme:tag1,tag2>。
请根据当前语气、情绪、关系感和互动氛围选择多个标签，而不是只用一个关键词。
例如：
才没有等你消息…<meme:shy,tease>
我只是有点困了。<meme:sleepy,care>
```

推荐标签：

```text
shy, tease, happy, proud, speechless, confused, angry, sad, sleepy, care, silent, refuse, comfort, excited, awkward
```

## 注意事项

- 图片 URL 必须可被 AstrBot 所在环境和消息协议端访问
- 插件不会使用数据库、Redis、WebUI、图床 SDK 或上传功能
- 如果 `meme_data.json` 不存在、格式错误、URL 非法或没有命中标签，插件会静默跳过发图，只保留清理后的文本
