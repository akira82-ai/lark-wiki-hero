#!/usr/bin/env python3
"""移除文档中的多余空行，保留段落间的单个空行"""

def remove_extra_blank_lines(content):
    """
    移除多余的空行，保留段落间的一个空行以维持阅读体验

    规则：
    1. 连续的多个空行（2个或更多）替换为单个空行
    2. 保留段落间的单个空行
    3. 代码块内部保持不变
    """
    lines = content.split('\n')
    result = []
    consecutive_blank = 0
    in_code_block = False
    code_fence = None

    for line in lines:
        # 检测代码块
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_fence = line.strip()
            else:
                in_code_block = False
                code_fence = None
            result.append(line)
            consecutive_blank = 0
            continue

        # 在代码块内，保持原样
        if in_code_block:
            result.append(line)
            consecutive_blank = 0
            continue

        # 检测空行
        if line.strip() == '':
            consecutive_blank += 1
            # 只保留连续空行的第一个
            if consecutive_blank == 1:
                result.append(line)
        else:
            # 非空行，重置计数器
            consecutive_blank = 0
            result.append(line)

    return '\n'.join(result)

# 测试文档内容
test_content = """# 满屏"不对"的绝望：我和AI编程的3天拉锯战

# 对话记录是自己的镜子

开发 airay-chat-export 技能时，我发现了一个被忽略的数据资产：我们的 AI 对话，是思维的快照。

## 01｜为什么写这个技能

### 对话丢失的瞬间

某天早上，我像往常一样打开 Claude Code，想找昨天的一段技术讨论。

找不到。

系统升级？会话过期？还是我记错了时间？

总之，那段包含着重要灵感的对话，就这样消失了。

这不是第一次。


每次重装系统、清理缓存，或者对话列表过长，那些"随时可以找到"的重要讨论，都会无声无息地消失。

更让我焦虑的是：这些对话不仅仅是"聊天记录"。

它们是思维的延伸、灵感的备忘录、知识的沉淀。

丢失它们，就像丢失了大脑的一部分。

我需要一个备份方案。

比如这段对话（来自开发记录）：

```markdown
❯ OK，我们在这个项目里面创建一个新的 Skill，这个 Skill 的名字等会再起，
   但我希望它能够完成任务呢，跟逻辑呢是获取指定日期内和指定关键字
   或指定项目的所有对话session记录，然后把它存到本地来，你可以参考
   Agent Review 这个 Skill 的逻辑。

⏺ 我来帮你规划这个新 Skill。首先让我探索一下 `airay-agent-review` 的实现逻辑，
  以及项目中对话 session 记录的存储方式。
```


这样的灵感记录，丢失了就找不回了。
"""

if __name__ == '__main__':
    processed = remove_extra_blank_lines(test_content)
    print("处理后的内容：")
    print("=" * 60)
    print(processed)
    print("=" * 60)
