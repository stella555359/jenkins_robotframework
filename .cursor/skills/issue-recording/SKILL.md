---
name: issue-recording
description: Create or update issue notes under the project issue folder when the user message begins with "issue". Use for issue-prefixed chats, issue tracking, Q&A logging, and keeping a markdown record of the user's problem and the assistant's answer in issue/.
---
# Issue Recording

## Purpose

When the user's message begins with `issue`, automatically create or update a markdown record in the project `issue/` directory.

The record should capture:

- the user's problem
- the assistant's answer
- important assumptions
- relevant files or follow-up items

Do this by default without asking the user whether to save the record.

## Language

Write issue records in Chinese by default.

This includes:

- the title
- section headings
- the question summary
- the answer summary
- next steps and notes

Keep filenames ASCII unless the user explicitly asks otherwise.

## Trigger

Apply this skill when any of these are true:

- the user message starts with `issue`
- the user explicitly asks to record an issue
- the user asks to save a Q&A record under `issue/`

If the message does not match these cases, do not use this skill.

## File Location

Save the record under:

`issue/`

Use a filename like:

`issue/YYYYMMDD-HHMM-short-slug.md`

Rules:

- prefer ASCII filenames
- keep the slug short and descriptive
- if a clean slug is not obvious, use `issue/YYYYMMDD-HHMM.md`
- if the current conversation is clearly continuing the same issue record, update the existing file instead of creating a second one

## Required Workflow

1. Read the user's `issue` message and identify the main problem.
2. Create the issue note as soon as there is enough context to name it.
3. After answering the user, update the same file so it includes the latest answer summary.
4. If the issue evolves in later turns of the same thread, append or revise the same note.
5. Do not log secrets, tokens, passwords, or internal credentials.

## Suggested Structure

Use this template:

```markdown
# 问题记录

- 创建时间: 2026-04-20 15:30
- 状态: open
- 触发词: issue <用户输入的原始内容>

## 问题

<用户问题摘要>

## 回答

<当前回答摘要>

## 相关文件

- `path/to/file`

## 后续动作

- <可选下一步>
```

## Authoring Notes

- The `Question` section should reflect the user's actual request, not a rewritten generic topic.
- The `Answer` section should be concise and should match what was actually told to the user.
- Use Chinese for the record body unless the user explicitly requests another language.
- If code changes were made, include the most relevant file paths.
- If no files were touched, omit `Relevant Files`.
- If there are no clear next steps, omit `Next Steps`.
- Keep the note practical and short.

## Examples

### Example Trigger

User message:

`issue Jenkins 反向代理后登录跳转异常`

Expected behavior:

- create a markdown note under `issue/`
- answer the user normally
- update the note with the final answer summary

### Example Filename

`issue/20260420-1530-jenkins-login-redirect.md`
