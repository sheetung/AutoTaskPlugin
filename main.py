from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from mirai import Image, Plain
import subprocess
import os
import re
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Union
from pathlib import Path

# 定时任务数据结构
class ScheduledTask:
    def __init__(self, name: str, time: str, launcher_type: str, launcher_id: int):
        self.name = name
        self.time = time
        self.launcher_type = launcher_type
        self.launcher_id = launcher_id

    def to_dict(self):
        return {
            "name": self.name,
            "time": self.time,
            "launcher_type": self.launcher_type,
            "launcher_id": self.launcher_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            time=data["time"],
            launcher_type=data["launcher_type"],
            launcher_id=data["launcher_id"]
        )

@register(name="AutoTaskPlugin", 
         description="支持定时任务的插件", 
         version="0.1", 
         author="sheetung")
class MyPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        self.host = host
        self.tasks_file = Path(__file__).parent / "scheduled_tasks.json"
        self.tasks: Dict[str, ScheduledTask] = {}
        self.load_tasks()
        asyncio.create_task(self.schedule_checker())

    def load_tasks(self):
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = {k: ScheduledTask.from_dict(v) for k, v in data.items()}
        except Exception as e:
            print(f"加载定时任务失败: {str(e)}")

    def save_tasks(self):
        try:
            with open(self.tasks_file, 'w') as f:
                data = {k: v.to_dict() for k, v in self.tasks.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"保存定时任务失败: {str(e)}")

    async def schedule_checker(self):
        while True:
            now = datetime.now().strftime("%H:%M")
            for task_name, task in list(self.tasks.items()):
                if task.time == now:
                    await self.execute_scheduled_task(task)
            await asyncio.sleep(60 - datetime.now().second)  # 每分钟检查一次

    async def execute_scheduled_task(self, task: ScheduledTask):
        script_path = Path(__file__).parent / "data" / f"{task.name}.py"
        if not script_path.exists():
            return

        try:
            result = subprocess.check_output(['python', str(script_path)], text=True, timeout=60)
            messages = self.convert_message(result, "system")
            
            await self.host.send_message(
                launcher_type=task.launcher_type,
                launcher_id=task.launcher_id,
                message=messages
            )
        except Exception as e:
            print(f"执行定时任务 {task.name} 失败: {str(e)}")

    @handler(PersonMessageReceived, GroupMessageReceived)
    async def handle_message(self, ctx: EventContext):
        msg = str(ctx.event.message_chain).strip()
        cleaned_msg = re.sub(r'@(\d+)', r' \1', msg).strip()
        cleaned_msg = re.sub(r'\s+', ' ', cleaned_msg)

        if cleaned_msg.startswith("定时 "):
            parts = cleaned_msg.split()
            if len(parts) < 2:
                return

            # 获取上下文信息
            launcher_type = "person" if isinstance(ctx.event, PersonMessageReceived) else "group"
            launcher_id = ctx.event.sender.group.id if launcher_type == "group" else ctx.event.sender.id

            if parts[1] == "删除":
                if len(parts) < 3:
                    return
                task_name = parts[2]
                if task_name in self.tasks:
                    del self.tasks[task_name]
                    self.save_tasks()
                    await ctx.reply(f"定时任务 {task_name} 已删除")
            else:
                if len(parts) < 3:
                    return
                task_name = parts[1]
                task_time = parts[2]
                
                # 验证时间格式
                if not re.match(r"^\d{1,2}:\d{2}$", task_time):
                    await ctx.reply("时间格式不正确，请使用 HH:mm 格式")
                    return

                # 标准化时间格式
                try:
                    hour, minute = map(int, task_time.split(':'))
                    task_time = f"{hour:02d}:{minute:02d}"
                except:
                    await ctx.reply("时间格式无效")
                    return

                self.tasks[task_name] = ScheduledTask(
                    name=task_name,
                    time=task_time,
                    launcher_type=launcher_type,
                    launcher_id=launcher_id
                )
                self.save_tasks()
                await ctx.reply(f"定时任务 {task_name} 已创建，每天 {task_time} 执行")

            ctx.prevent_default()

    def convert_message(self, message: str, sender_id: str) -> List[Union[Plain, Image, At]]:
        parts = []
        last_end = 0
        image_pattern = re.compile(r'!\[.*?\]\((https?://\S+)\)')

        # 处理@指令
        if "atper_on" in message:
            parts.append(At(target=sender_id))
            message = message.replace("atper_on", "")

        # 处理图片
        for match in image_pattern.finditer(message):
            start, end = match.span()
            if start > last_end:
                parts.append(Plain(message[last_end:start]))
            image_url = match.group(1)
            parts.append(Image(url=image_url))
            last_end = end

        # 处理剩余文本
        if last_end < len(message):
            parts.append(Plain(message[last_end:]))

        return parts if parts else [Plain("任务执行完成")]

    def __del__(self):
        self.save_tasks()