# 错题本 · WrongBook

把刷题时做错的题集中记下来，复盘时按标签查找，统计页一眼看出自己哪个知识点最弱。

**当前状态**：骨架阶段。列表页和详情页已经能跑（真实的数据库读写），登录和增删改还待实现。

> 在线 Demo：待部署

---

## 功能进度

- [x] 错题列表（标签 / 难度 / 时间）
- [x] 错题详情
- [ ] 新增错题
- [ ] 编辑 / 删除
- [ ] 注册 / 登录 / 权限隔离
- [ ] 搜索 + 标签筛选
- [ ] 统计页（薄弱知识点 Top3）

---

## 技术栈

| 层 | 选型 |
|---|---|
| 语言 | Python 3.13 |
| Web 框架 | Flask 3 |
| 数据库 | SQLite（Python 标准库 `sqlite3`，手写 SQL） |
| 模板 | Jinja2 |
| 样式 | Bootstrap 5（CDN） |
| 测试 | pytest |

---

## 快速开始

> **偷懒办法**：双击桌面上的「错题本」快捷方式（或项目根目录的 `start.bat`），
> 会自动启动服务并在 3 秒后打开浏览器。关掉那个黑窗口就是停止服务。
> 下面的手动步骤用于理解原理，以及换电脑时照着做。

```powershell
# 1. 进入项目目录
cd E:\deepseek\wrongbook

# 2. 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 复制配置模板
copy .env.example .env

# 5. 初始化数据库（生成 wrongbook.db 并写入 6 条演示数据）
python seed.py

# 6. 启动
python app.py
```

然后浏览器打开 <http://127.0.0.1:5000>

停止服务：在终端按 `Ctrl + C`。

---

## 目录结构

```
wrongbook/
├── app.py                # 入口：创建 app、注册蓝图、错误页
├── config.py             # 配置：密钥、数据库路径、调试开关
├── db.py                 # 数据库访问层（所有 SQL 调用都走这里）
├── schema.sql            # 建表语句（唯一真相来源）
├── seed.py               # 重建数据库 + 写演示数据
├── requirements.txt      # 依赖清单
├── pytest.ini            # pytest 配置
├── .env.example          # 配置模板（.env 不提交）
├── routes/               # 路由层：一个文件一组页面
│   ├── auth.py           # 注册 / 登录 / 登出
│   ├── records.py        # 错题增删改查
│   └── stats.py          # 统计
├── templates/            # Jinja2 模板
│   ├── base.html         # 所有页面的骨架
│   ├── record_list.html
│   ├── record_detail.html
│   ├── placeholder.html  # 未实现功能的占位页
│   └── errors/           # 404 / 500
├── static/style.css
├── tests/                # pytest 测试
└── docs/                 # 文档
```

---

## 数据库设计

4 张表，`records` 与 `tags` 是多对多，靠 `record_tags` 关联：

| 表 | 作用 |
|---|---|
| `users` | 账号，密码只存哈希 |
| `records` | 一条错题：标题、题面、代码、错误原因、难度 |
| `tags` | 标签（DP、二分、BFS…） |
| `record_tags` | 记录 ↔ 标签的关联表 |

详细字段见 `schema.sql`。设计说明（ER 图、字段含义、为什么这样拆表）由你自己补到 `docs/02-数据库设计.md`，这是简历上能讲的东西。

---

## 常用命令

```powershell
python seed.py        # 重建数据库（会清空数据！）
python app.py         # 启动开发服务器
pytest                # 跑测试
pytest -v             # 跑测试并显示每个用例名
```

---

## 开发记录

> 这里记 2~3 个你实际踩过的坑，面试时能直接讲。格式：现象 → 原因 → 怎么解决的。

（待填写）

---

## 后续计划

见 `docs/下一步任务.md`。
