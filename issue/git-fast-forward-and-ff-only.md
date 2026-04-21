# Git Fast-Forward 与 `--ff-only` 说明

## 1. 什么是 fast-forward

`fast-forward` 可以理解成：

- 你的当前分支没有分叉历史
- 只是单纯落后于目标分支
- Git 只需要把分支指针直接往前移动
- 不需要新建 merge commit

例如：

```text
A --- B --- C   main
          \
           D --- E   feature/agent-setup
```

如果你当前在 `main`，想把 `feature/agent-setup` 合进来，而 `main` 还停在 `C`，那么 Git 可以直接把 `main` 指到 `E`：

```text
A --- B --- C --- D --- E   main, feature/agent-setup
```

这就叫 `fast-forward`。

它的特点是：

- 历史是直线的
- 没有额外 merge commit
- 看起来像 `main` 只是“往前走了几步”

## 2. 什么是 `git pull --ff-only origin main`

`git pull` 本质上等于：

```bash
git fetch origin
git merge origin/main
```

而：

```bash
git pull --ff-only origin main
```

表示：

- 先从远端取最新信息
- 然后只允许用 fast-forward 的方式更新当前分支
- 如果做不到 fast-forward，就直接失败
- 不允许 Git 偷偷帮你做自动 merge

所以它特别适合这种场景：

- 你只是想把本地 `main` 同步成远端最新 `main`
- 你不想在不知情的情况下生成 merge commit

## 3. `git pull origin main` 和 `git pull --ff-only origin main` 的区别

### `git pull origin main`

特点：

- 更宽松
- 如果能 fast-forward，就 fast-forward
- 如果不能 fast-forward，Git 会尝试自动 merge
- merge 成功后，可能生成一个新的 merge commit

示意图：

```text
A --- B --- C   origin/main
       \
        D       main
```

这时执行：

```bash
git pull origin main
```

Git 可能会得到：

```text
A --- B --- C   origin/main
       \     \
        D --- M   main
```

这里的 `M` 就是自动生成的 merge commit。

### `git pull --ff-only origin main`

特点：

- 更严格
- 只允许纯快进
- 只要本地和远端发生分叉，就报错退出
- 不会生成 merge commit

对于想保持 `main` 历史干净的人，这个更安全。

## 4. 什么情况下 `--ff-only` 会失败

`--ff-only` 失败的本质原因只有一个：

- 当前分支和目标分支已经分叉了
- Git 不能只靠“移动指针”完成更新

最常见是这种情况：

```text
A --- B --- C   origin/main
       \
        D --- E   main
```

这里：

- 远端 `main` 有新提交 `C`
- 你本地 `main` 也有自己的提交 `D`、`E`
- 两边不再是单线关系

这时执行：

```bash
git pull --ff-only origin main
```

就会失败。

原因不是 Git 坏了，而是它在保护你：

- 它拒绝在你没明确表态时自动制造 merge commit

## 5. `git fetch origin` 在 checkout 前有什么作用

`git fetch origin` 的作用是：

- 更新你本地对远端分支状态的认知
- 刷新 `origin/main`、`origin/feature/agent-setup` 这些远端跟踪分支
- 但不改你当前所在分支
- 也不改工作区文件

可以把它理解成：

- 先更新远端情报
- 再决定下一步怎么操作

例如你准备合并前，先执行：

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git merge origin/feature/agent-setup
```

好处是：

- 你拿到的是最新的 `origin/main`
- 你拿到的是最新的 `origin/feature/agent-setup`
- 后续 merge 不是基于旧快照做判断

## 6. 最推荐的日常习惯

如果你的目标是：

- 主分支历史尽量干净
- 不希望 Git 默默替你自动 merge

那么推荐习惯是：

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
```

然后再按需要执行：

```bash
git merge feature/agent-setup
```

或者：

```bash
git merge origin/feature/agent-setup
```

## 7. 一句话记忆

- `fetch`：只更新远端信息，不改当前分支
- `pull`：更新远端信息后，顺手更新当前分支
- `pull --ff-only`：只允许安全快进，不允许自动 merge
- `fast-forward`：没有分叉，只是把分支指针往前移

## 8. 结合这次 `feature/agent-setup -> main` 的实际命令示例

如果你这次要做的是：

- 把 `feature/agent-setup` 合到 `main`
- 并且希望先把本地 `main` 和远端 `main` 对齐
- 再进行明确、可控的合并

那么推荐按下面顺序执行：

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git merge feature/agent-setup
git push origin main
```

这 5 步分别在做什么：

### 第 1 步

```bash
git fetch origin
```

作用：

- 刷新远端最新状态
- 更新本地的 `origin/main`
- 更新本地的 `origin/feature/agent-setup`

这一步不会改你当前分支，也不会改工作区。

### 第 2 步

```bash
git checkout main
```

作用：

- 切到你准备接收合并的目标分支 `main`

因为你要把功能分支合到 `main`，所以真正执行 merge 的位置应该在 `main` 上，而不是在 `feature/agent-setup` 上。

### 第 3 步

```bash
git pull --ff-only origin main
```

作用：

- 先把本地 `main` 更新到远端最新 `main`
- 只允许快进更新
- 不允许 Git 偷偷生成 merge commit

这一句的目标不是“合功能分支”，而是先把 `main` 打扫干净，确保你接下来是在一个最新、干净的 `main` 上做 merge。

### 第 4 步

```bash
git merge feature/agent-setup
```

作用：

- 把功能分支的提交正式合入当前的 `main`

如果你的本地 `feature/agent-setup` 已经是最新，这样写就可以。

如果你担心本地功能分支不是最新，也可以写成：

```bash
git merge origin/feature/agent-setup
```

这样就是明确按远端最新分支来合。

### 第 5 步

```bash
git push origin main
```

作用：

- 把已经完成 merge 的本地 `main` 推到远端

到这一步，远端 `main` 才真正完成更新。

## 9. 这组命令为什么比直接 `git pull origin main` 后再乱合更稳

因为它把动作拆得很清楚：

1. 先刷新远端信息
2. 再切到目标分支
3. 先确保目标分支和远端主线干净对齐
4. 再明确执行功能分支合并
5. 最后再 push

这样做的好处是：

- 每一步目的都很明确
- 更容易看出问题出在哪一步
- 不容易在同步 `main` 时意外制造 merge commit
- 更适合主分支要保持清晰历史的团队

## 10. 合并完成后删除本地 / 远端 feature 分支

如果你已经确认下面这些条件都成立：

- `feature/agent-setup` 已经成功合入 `main`
- `main` 已经 `push` 到远端
- 这个功能分支后面不再继续复用

那么可以顺手把功能分支删掉。

### 删除本地分支

```bash
git branch -d feature/agent-setup
```

作用：

- 删除本地 `feature/agent-setup`
- 只有在 Git 判断它已经合并完成时才会删除

如果 Git 提示还没有合并，不要急着改成强删，先确认是不是确实还没合到 `main`。

### 删除远端分支

```bash
git push origin --delete feature/agent-setup
```

作用：

- 删除远端仓库上的 `feature/agent-setup`

这样做之后，团队里其他人下次 `fetch` 时，也会看到这个远端功能分支已经被移除。

### 对应这次场景的完整收尾命令

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git merge feature/agent-setup
git push origin main
git branch -d feature/agent-setup
git push origin --delete feature/agent-setup
```

### 一句话判断

- `git branch -d ...` 是删本地分支
- `git push origin --delete ...` 是删远端分支
- 通常先确认 `main` 已经 push 成功，再删分支更稳