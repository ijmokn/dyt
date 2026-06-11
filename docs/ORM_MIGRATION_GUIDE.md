# 数据库 ORM 重构指南

## 概述

项目已从原生 SQL 查询重构为 SQLAlchemy ORM 模式，提供了更好的类型安全、代码可维护性和数据库迁移支持。

## 主要变更

### 1. 新增文件

- `src/server/core/database.py` - 数据库配置和会话管理
- `src/server/models/__init__.py` - ORM 模型定义
- `src/server/alembic/` - 数据库迁移配置和脚本
- `src/server/alembic.ini` - Alembic 配置文件

### 2. 修改文件

- `src/server/api/routes/chat_history.py` - 使用 ORM 查询替代原生 SQL
- `src/server/requirements.txt` - 添加 `alembic==1.15.0`

## ORM 模型

定义了以下模型（在 `models/__init__.py`）:

- **User** - 用户信息
- **Conversation** - 会话信息
- **Message** - 消息内容
- **ConversationTag** - 会话标签（可选）
- **MessageReference** - 消息引用关系（可选）

## 使用方法

### 安装依赖

```bash
cd src/server
pip install -r requirements.txt
```

### 数据库迁移

#### 方式 1: 使用 Alembic（推荐）

```bash
# 1. 创建初始迁移
cd src/server
alembic revision --autogenerate -m "Initial migration"

# 2. 应用迁移
alembic upgrade head

# 3. 查看当前版本
alembic current

# 4. 查看历史
alembic history
```

#### 方式 2: 直接创建表（开发环境）

```python
from core.database import init_db
init_db()  # 直接创建所有表
```

### 在代码中使用 ORM

#### 依赖注入方式（推荐）

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models import User, Conversation

@router.get("/conversations")
async def get_conversations(db: Session = Depends(get_db)):
    # 查询示例
    conversations = db.query(Conversation).filter(
        Conversation.status == "active"
    ).all()
    
    return conversations
```

#### 查询示例

```python
# 1. 简单查询
user = db.query(User).filter(User.email == "user@example.com").first()

# 2. 关联查询
conversations = db.query(Conversation).join(User).filter(
    User.email == "user@example.com"
).all()

# 3. 搜索查询
results = db.query(Conversation).filter(
    Conversation.title.ilike(f"%{keyword}%")
).all()

# 4. 分页查询
conversations = db.query(Conversation).offset(0).limit(20).all()

# 5. 排序
conversations = db.query(Conversation).order_by(
    Conversation.updated_at.desc()
).all()
```

#### 创建和更新

```python
# 创建
new_user = User(email="test@example.com", nickname="Test User")
db.add(new_user)
db.commit()
db.refresh(new_user)  # 获取生成的 ID

# 更新
user = db.query(User).filter(User.id == 1).first()
user.nickname = "New Nickname"
user.updated_at = datetime.now(timezone.utc)
db.commit()

# 删除（级联删除相关记录）
conversation = db.query(Conversation).filter(Conversation.id == "conv_123").first()
db.delete(conversation)
db.commit()
```

## 优势对比

### 之前（原生 SQL）

```python
# ❌ 字段名容易拼错
result = db.execute(text("SELECT id, email FROM users WHERE email = :email"), {"email": email})
row = result.fetchone()
user_id = row[0]  # 数字索引，容易出错

# ❌ 没有类型提示
# ❌ SQL 注入风险（如果不小心）
# ❌ 难以维护
```

### 现在（ORM）

```python
# ✅ 类型安全
user = db.query(User).filter(User.email == email).first()
user_id = user.id  # IDE 有类型提示

# ✅ 防止 SQL 注入
# ✅ 自动处理关联关系
# ✅ 易于重构
```

## 迁移现有数据

如果你已经有数据库表：

1. **备份现有数据**
   ```bash
   pg_dump -U postgres -d your_db > backup.sql
   ```

2. **使用 Alembic 标记当前状态**
   ```bash
   alembic stamp head
   ```

3. **后续变更使用 Alembic 管理**
   ```bash
   alembic revision --autogenerate -m "Add new column"
   alembic upgrade head
   ```

## 常见问题

### Q: 数据库连接从哪里配置？

A: 通过环境变量 `DATABASE_URL`，格式：
```
postgresql://user:password@host:port/database
```

### Q: 如何处理事务？

A: FastAPI 的依赖注入已自动处理：
```python
async def my_endpoint(db: Session = Depends(get_db)):
    try:
        # 操作数据库
        db.add(new_object)
        db.commit()
    except Exception:
        db.rollback()
        raise
```

### Q: 如何添加新字段？

A: 
1. 修改 `models/__init__.py` 中的模型
2. 运行 `alembic revision --autogenerate -m "Add new field"`
3. 检查生成的迁移脚本
4. 运行 `alembic upgrade head`

### Q: 性能会下降吗？

A: 
- ORM 有轻微开销，但通过连接池和查询优化可以忽略
- 复杂查询仍可使用原生 SQL：`db.execute(text("SELECT ..."))`
- 使用 `joinedload`/`selectinload` 避免 N+1 查询

## 测试

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base

# 创建测试数据库
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
TestSession = sessionmaker(bind=engine)

def test_create_user():
    db = TestSession()
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    assert user.id is not None
```

## 参考文档

- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [FastAPI 数据库最佳实践](https://fastapi.tiangolo.com/tutorial/sql-databases/)
