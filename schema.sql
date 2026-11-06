-- =============================================================
-- 错题本 数据库结构（唯一真相来源）
-- 改完这里，重新跑一次 `python seed.py` 让变更生效
-- 注意：seed.py 会先删除数据库文件，本地数据会丢
-- =============================================================

PRAGMA foreign_keys = ON;

-- 按依赖倒序删表，避免外键报错
DROP TABLE IF EXISTS record_tags;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS records;
DROP TABLE IF EXISTS users;

-- 用户表：登录用
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,          -- 用户名，唯一
    password_hash TEXT    NOT NULL,                 -- 密码哈希，绝不存明文
    created_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 错题记录表：一条 = 一道做错/值得复盘的题
CREATE TABLE records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,                    -- 归属用户，权限隔离靠它
    title      TEXT    NOT NULL,                    -- 题目名称
    content    TEXT,                                -- 题面 / 思路摘要
    code       TEXT,                                -- 我写错的那段代码
    reason     TEXT,                                -- 当时为什么错（复盘核心）
    difficulty INTEGER NOT NULL DEFAULT 3
               CHECK (difficulty BETWEEN 1 AND 5),  -- 难度 1~5
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 标签表
CREATE TABLE tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 关联表：一条记录可以挂多个标签（多对多）
CREATE TABLE record_tags (
    record_id INTEGER NOT NULL,
    tag_id    INTEGER NOT NULL,
    PRIMARY KEY (record_id, tag_id),
    FOREIGN KEY (record_id) REFERENCES records (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)    REFERENCES tags (id)    ON DELETE CASCADE
);

-- 索引：列表页永远按 user_id 过滤、按时间倒序，这两条很常用
CREATE INDEX idx_records_user    ON records (user_id);
CREATE INDEX idx_records_created ON records (created_at DESC);
