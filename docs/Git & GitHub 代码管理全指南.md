# 从零到精通：Git & GitHub 代码管理全指南

## 一、 核心原理篇

要掌握 Git，首先要理解它的核心架构。Git 是一个**分布式版本控制系统**，而 GitHub 是一个**托管 Git 仓库的云端服务平台**。

### 1. Git 的三个工作区域
Git 本地数据管理分为三个主要区域，这是理解所有命令的基础：
1. **工作区 (Working Directory)**：你当前在电脑上能看到的项目目录和文件。
2. **暂存区 (Staging Area / Index)**：一个包含下次将要提交的文件列表的“缓存区”。
3. **本地仓库 (Local Repository)**：Git 保存项目所有历史版本的地方（即隐藏的 `.git` 目录）。

### 2. 文件的四种状态
- **Untracked (未跟踪)**：新创建的文件，Git 还没开始管理它。
- **Modified (已修改)**：被 Git 管理的文件发生了更改，但还没放到暂存区。
- **Staged (已暂存)**：修改后的文件已经被放入暂存区，准备好在下次提交时保存。
- **Unmodified (未修改)**：文件自上次提交后没有发生任何变化。

---

## 二、 基础配置与起步

### 1. 全局配置
安装 Git 后，第一步是配置你的身份信息（每次提交都会带上这个信息）：
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 2. 创建或获取仓库
**情况 A：从零初始化一个本地项目**
```bash
cd your_project_folder
git init          # 初始化仓库，生成 .git 文件夹
```

**情况 B：从 GitHub 克隆一个已有项目**
```bash
git clone https://github.com/username/repository.git
```

---

## 三、 日常单人工作流

日常写代码最常用的“三步曲”：**修改代码 -> 暂存 -> 提交**。

### 1. 查看当前状态
```bash
git status        # 随时运行此命令，查看哪些文件被修改、哪些在暂存区
```

### 2. 添加到暂存区 (Staged)
```bash
git add file.txt  # 暂存单个文件
git add .         # 暂存当前目录下所有修改和新增的文件（最常用）
```

### 3. 提交到本地仓库 (Local Repo)
```bash
git commit -m "feat: 添加了用户登录功能"   # -m 后面是提交说明，要求简明扼要
```

### 4. 查看提交历史
```bash
git log           # 查看详细历史
git log --oneline # 查看简化的单行历史
```

---

## 四、 分支管理 (Branching)

分支是 Git 的杀手锏功能。它允许你在不影响主线（通常是 `main` 或 `master`）的情况下开发新功能或修复 Bug。

### 1. 分支基础操作
```bash
git branch                 # 查看本地所有分支，当前分支前会有 * 号
git branch feature-login   # 创建名为 feature-login 的新分支
git checkout feature-login # 切换到该分支
# 或者使用更现代的命令：
git switch feature-login   # 切换分支
git switch -c feature-login # 创建并立即切换到新分支（最常用）
```

### 2. 合并分支
当你在 `feature-login` 分支开发完毕后，需要将其合并回 `main`：
```bash
git switch main            # 1. 先切回主分支
git merge feature-login    # 2. 将目标分支合并到当前分支
```

### 3. 删除分支
```bash
git branch -d feature-login # 删除已合并的本地分支
```

---

## 五、 GitHub 远程协作与功能

### 1. 关联远程仓库
如果你是本地先 `git init` 的项目，需要将其与 GitHub 空仓库关联：
```bash
git remote add origin https://github.com/username/repository.git
git branch -M main         # 确保主分支名为 main
git push -u origin main    # 首次推送并建立追踪关系 (-u)
```

### 2. 日常同步 (Push & Pull)
```bash
git push origin main       # 将本地 main 分支的代码推送到 GitHub
git pull origin main       # 从 GitHub 拉取最新代码并与本地合并
```

### 3. GitHub 核心协作流：Pull Request (PR)
在团队开发或开源贡献中，通常不直接 push 到 `main` 分支，而是：
1. **Fork**：在 GitHub 上将别人的仓库复制到自己的账号下。
2. **Clone**：将自己账号下的仓库克隆到本地。
3. **Branch**：创建一个新分支（如 `fix-bug`）。
4. **Commit & Push**：提交代码并 push 到自己的 GitHub 仓库。
5. **Pull Request**：在 GitHub 页面点击 "New Pull Request"，请求原仓库作者合并你的代码。
6. **Review & Merge**：代码审查通过后，项目维护者会将其 Merge 到主仓库。

---

## 六、 进阶与急救指南 (Advanced & Rescue)

当你代码写乱了或者提交错了，不要慌，Git 提供了强大的后悔药。

### 1. 丢弃工作区的修改 (还没 git add)
```bash
git checkout -- file.txt   # 撤销对特定文件的修改，恢复到上次提交的状态
git restore file.txt       # (新版 Git 推荐命令) 作用同上
```

### 2. 撤销暂存 (已经 git add，但没 git commit)
```bash
git reset HEAD file.txt    # 将文件移出暂存区，但保留你的修改
git restore --staged file.txt # (新版 Git 推荐命令) 作用同上
```

### 3. 撤销提交 (已经 git commit)
```bash
# 软撤销：撤销 commit，但保留代码修改在工作区
git reset --soft HEAD~1    

# 硬撤销：撤销 commit，并且丢弃所有代码修改（危险操作！）
git reset --hard HEAD~1    

# 修正最后一次提交（比如漏提了文件或写错了注释）
git commit --amend -m "新的正确注释"
```

### 4. 暂存工作现场 (Stash)
当你在 A 分支开发到一半，突然需要切到 B 分支修紧急 Bug，但 A 分支的代码还没写完不能 commit 时：
```bash
git stash                  # 将当前工作区的修改暂时“藏”起来
# ... 切换到别的分支去工作，完成后切回来 ...
git stash pop              # 恢复刚才“藏”起来的修改
```

### 5. 变基 (Rebase) —— 让历史更整洁
Rebase 是 Merge 的替代品。Merge 会产生一个分叉合并节点，而 Rebase 会把你的分支提交“移动”到目标分支的最前端，保持历史是一条直线。
```bash
git switch feature-branch
git rebase main            # 将当前分支变基到 main 分支之上
```
*⚠️ 黄金法则：永远不要在公共的（已经 push 到远端的）分支上执行 rebase！*

### 6. 解决冲突 (Merge Conflict)
当两个分支修改了同一个文件的同一行代码，合并时就会产生冲突。
1. Git 会提示冲突，并在冲突文件里标记 `<<<<<<<`、`=======`、`>>>>>>>`。
2. 你需要手动打开文件，保留需要的代码，删除 Git 添加的标记符号。
3. 解决后：
```bash
git add 解决好冲突的文件
git commit -m "fix: 解决合并冲突"
```

---

## 七、 `.gitignore` 文件
在项目根目录创建一个 `.gitignore` 文件，写在里面的文件或目录，Git 会自动忽略，永远不会被提交。
**常用配置示例：**
```text
# 忽略系统文件
.DS_Store
Thumbs.db

# 忽略依赖文件夹
node_modules/
__pycache__/

# 忽略编译生成的文件
*.class
*.o
/dist

# 忽略本地环境变量和密钥
.env
```