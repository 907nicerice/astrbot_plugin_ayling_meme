# astrbot_plugin_meme_online

支持 LLM 多标签语义选择表情包，而不是传统关键词触发。

让角色扮演 Bot 通过 `<meme:shy,tease>` 输出多标签表情意图，插件自动匹配图床表情包并发送。
适用于陪伴、人格化、QQ 拟真聊天场景。

本仓库内实际插件目录为：

```text
astrbot_plugin_ayling_meme/
```

## 核心卖点

- 支持 LLM 输出多标签语义标记，而不是死板的单关键词触发
- 表情意图和回复文本解耦，适合角色扮演和人格化对话
- 使用外部图床 URL 发送表情包，不依赖本地图库
- 发送前自动清理 `<meme:...>` 标记，用户不会看到控制标签
- 轻量、无数据库、无 Redis，适合低内存服务器部署

例如：

```text
才没有等你消息…<meme:shy,tease>
```

最终会发送：

- 文本：`才没有等你消息…`
- 图片：一张语义上更接近 `shy + tease` 的表情包

## 仓库结构

```text
.
├─ README.md
└─ astrbot_plugin_ayling_meme/
   ├─ metadata.yaml
   ├─ main.py
   ├─ meme_data.json
   └─ README.md
```

## 安装方法

把仓库中的 `astrbot_plugin_ayling_meme/` 整个目录复制到：

```text
AstrBot/data/plugins/astrbot_plugin_ayling_meme/
```

不要只复制单个文件。

## meme_data.json 格式

插件使用外部图床 URL，不依赖本地图片，不使用数据库，不使用 Redis。

示例：

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

- `url`：必须是 `http` 或 `https` 开头
- `tags`：字符串数组
- `weight`：可选，默认按 `1` 处理，用于加权随机

## LLM Prompt 用法

你可以在 AstrBot 的人格提示词或系统提示词里写：

```text
当语气适合发送表情包时，在回复结尾附加一个表情标记，格式为 <meme:tag1,tag2>。
请根据角色当前情绪、语气、关系感和互动氛围选择多个标签，而不是只用一个关键词。
例如：
才没有等你消息…<meme:shy,tease>
我只是有点困了。<meme:sleepy,care>
```

推荐标签：

```text
shy, tease, happy, proud, speechless, confused, angry, sad, sleepy, care, silent, refuse, comfort, excited, awkward
```

## 注意事项

- 只使用第一组 `<meme:...>` 作为选图依据，但会移除消息中的所有标记
- 如果没有匹配图片、配置文件损坏、URL 非法或功能开关关闭，插件只会发送清理后的文本
- 图片 URL 必须能被 AstrBot 所在环境和协议端正常访问
- 本插件使用 `on_decorating_result` 钩子修改最终消息链，适合低内存部署
