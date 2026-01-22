"""测试上下文压缩和 Token 窗口管理效果。"""

import asyncio
import time

from mas.context.manager import ContextManager
from mas.context.types import ContextLayer, ContextType


async def main() -> None:
    print("=" * 60)
    print("上下文压缩与 Token 窗口管理测试")
    print("=" * 60)

    # 创建上下文管理器（无 LLM，测试智能截断回退）
    manager = ContextManager(session_id="test-session", llm_client=None, max_tokens=2000)

    # 模拟任务 1：生成长输出（需求分析）
    long_output_1 = """
## 需求分析报告

### 1. 功能需求
1.1 用户管理模块
- 用户注册：支持邮箱、手机号注册
- 用户登录：支持密码登录、OAuth2.0 第三方登录
- 用户信息管理：个人资料编辑、头像上传

1.2 待办事项模块
- 创建待办：标题、描述、优先级、截止日期
- 查询待办：支持分页、筛选、搜索
- 更新待办：修改任意字段、标记完成
- 删除待办：软删除，支持回收站

1.3 标签模块
- 标签创建与管理
- 待办与标签的多对多关联

### 2. 非功能需求
2.1 性能要求
- API 响应时间 < 200ms
- 支持 1000 并发用户

2.2 安全要求
- JWT Token 认证
- 数据加密存储
- SQL 注入防护

### 3. 技术选型
- 后端框架：FastAPI
- 数据库：PostgreSQL
- 缓存：Redis
- 文档：OpenAPI 3.0

### 4. 数据库设计
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE todos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 0,
    due_date TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

这是一个完整的需求分析文档，包含了所有必要的功能点和技术细节。
""".strip()

    print(f"\n任务 1 输出长度: {len(long_output_1)} 字符")

    # 添加任务 1 输出
    entry_id_1 = await manager.add_task_output(
        task_id="requirements",
        output=long_output_1,
        agent_name="planner-agent",
        dependent_task_ids=["implementation"],
    )
    print(f"任务 1 上下文 ID: {entry_id_1}")

    # 检查是否被压缩
    entry_1 = manager.store.get(entry_id_1)
    if entry_1:
        print(f"任务 1 压缩状态: {'已压缩' if entry_1.is_compressed else '未压缩'}")
        if entry_1.is_compressed:
            print(f"  原始长度: {entry_1.original_length}")
            print(f"  摘要长度: {len(entry_1.summary or '')}")

    # 模拟任务 2：生成更长的输出（代码实现）
    long_output_2 = """
## 代码实现

### main.py
```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, crud
from database import get_db

app = FastAPI(title="待办事项 API", version="1.0.0")

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/todos/", response_model=List[schemas.Todo])
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    todos = crud.get_todos(db, skip=skip, limit=limit)
    return todos

@app.post("/todos/", response_model=schemas.Todo)
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db=db, todo=todo)

@app.put("/todos/{todo_id}", response_model=schemas.Todo)
def update_todo(todo_id: int, todo: schemas.TodoUpdate, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return crud.update_todo(db=db, todo_id=todo_id, todo=todo)

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    crud.delete_todo(db=db, todo_id=todo_id)
    return {"message": "Todo deleted successfully"}
```

### models.py
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    todos = relationship("Todo", back_populates="owner")

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    priority = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="todos")
```

### schemas.py
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 0

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    completed: Optional[bool] = None

class Todo(TodoBase):
    id: int
    completed: bool
    user_id: int
    class Config:
        from_attributes = True
```

代码实现完成，包含完整的 CRUD 操作和数据模型定义。
""".strip()

    print(f"\n任务 2 输出长度: {len(long_output_2)} 字符")

    entry_id_2 = await manager.add_task_output(
        task_id="implementation",
        output=long_output_2,
        agent_name="backend-agent",
        dependent_task_ids=["review"],
    )
    print(f"任务 2 上下文 ID: {entry_id_2}")

    entry_2 = manager.store.get(entry_id_2)
    if entry_2:
        print(f"任务 2 压缩状态: {'已压缩' if entry_2.is_compressed else '未压缩'}")
        if entry_2.is_compressed:
            print(f"  原始长度: {entry_2.original_length}")
            print(f"  摘要长度: {len(entry_2.summary or '')}")

    # 测试上下文检索（模拟任务 3 获取依赖上下文）
    print("\n" + "-" * 60)
    print("模拟任务 3 (review) 获取上下文:")
    print("-" * 60)

    context_str = await manager.get_context_for_task(
        task_id="review",
        dependency_ids=["requirements", "implementation"],
        max_tokens=2000,
    )

    print(f"\n上下文总长度: {len(context_str)} 字符")
    print(f"上下文 Token 估算: {manager.window.count_tokens(context_str)}")

    print("\n上下文内容预览 (前 500 字符):")
    print("-" * 40)
    print(context_str[:500] + "..." if len(context_str) > 500 else context_str)

    # 打印统计
    print("\n" + "=" * 60)
    print("最终统计")
    print("=" * 60)

    stats = manager.get_stats()
    print(f"总条目数: {stats['total_entries']}")
    print(f"总 Token 估算: {stats['token_estimate']}")

    # 检查访问计数
    print("\n访问计数:")
    task_layer = manager.store.get_layer(ContextLayer.TASK)
    for key, entry in task_layer.items():
        print(f"  - {entry.source}: 访问 {entry.access_count} 次, 重要性 {entry.importance:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
