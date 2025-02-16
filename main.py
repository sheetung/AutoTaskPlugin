import threading
import asyncio
import json
import time
import logging
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from mirai import MessageChain, Plain

# 定义全局变量
timer_thread = None
stop_timer_thread = False

# 定时任务配置文件路径
TIMER_CONFIG_FILE = "timer_config.json"

# {
#     "tasks": [
#         {
#             "command": "#定时任务1",
#             "interval": 60,  // 每60秒触发一次
#             "message": "这是定时任务1的提醒消息",
#             "reply_type": "person",  // 回复类型：个人
#             "target_id": 123456789  // 目标个人ID
#         },
#         {
#             "command": "#定时任务2",
#             "interval": 300,  // 每5分钟触发一次
#             "message": "这是定时任务2的提醒消息",
#             "reply_type": "group",  // 回复类型：群组
#             "target_id": 987654321  // 目标群组ID
#         }
#     ]
# }

@register(name="AutoTaskPlugin", description="定时任务插件", version="0.1", author="sheetung")
class TimerPlugin(BasePlugin):
    def __init__(self, host: APIHost):
        self.logger = logging.getLogger(__name__)
        self.tasks = self.load_timer_config()

    def load_timer_config(self):
        """加载定时任务配置"""
        try:
            with open(TIMER_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("tasks", [])
        except Exception as e:
            self.logger.error(f"加载定时任务配置失败: {e}")
            return []

    @handler(PersonMessageReceived)
    @handler(GroupMessageReceived)
    async def person_normal_message_received(self, ctx: EventContext, **kwargs):
        global timer_thread
        receive_text = ctx.event.text_message

        if receive_text == "#启动定时任务":
            if timer_thread is None or not timer_thread.is_alive():
                timer_thread = threading.Thread(target=self.run_timer_tasks, args=(ctx,), daemon=True)
                timer_thread.start()
                await ctx.event.query.adapter.reply_message(ctx.event.query.message_event, [("定时任务已启动")], False)
            else:
                await ctx.event.query.adapter.reply_message(ctx.event.query.message_event, [("定时任务已在运行中")], False)
            ctx.prevent_default()
        elif receive_text == "#停止定时任务":
            if timer_thread is not None and timer_thread.is_alive():
                global stop_timer_thread
                stop_timer_thread = True
                timer_thread.join()
                await ctx.event.query.adapter.reply_message(ctx.event.query.message_event, [("定时任务已停止")], False)
            else:
                await ctx.event.query.adapter.reply_message(ctx.event.query.message_event, [("定时任务未启动")], False)
            ctx.prevent_default()

    def run_timer_tasks(self, ctx):
        """运行定时任务"""
        global stop_timer_thread
        while not stop_timer_thread:
            for task in self.tasks:
                command = task.get("command")
                interval = task.get("interval")
                message = task.get("message")
                reply_type = task.get("reply_type", "person")  # 默认回复给个人
                target_id = task.get("target_id")  # 获取目标ID
                if command and interval and message and target_id:
                    asyncio.run(self.send_message(ctx, command, message, reply_type, target_id))
                    time.sleep(interval)

    async def send_message(self, ctx, command, message, reply_type, target_id):
        """发送消息"""
        try:
            if reply_type == "person":
                # 回复给个人
                await ctx.event.query.adapter.reply_message(ctx.event.query.message_event, [(message)], False)
            elif reply_type == "group":
                # 回复给群组
                await ctx.send_message(target_type='group', target_id=target_id, message=message)
            else:
                self.logger.error(f"未知的回复类型: {reply_type}")
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")

    def __del__(self):
        global stop_timer_thread
        stop_timer_thread = True
        if timer_thread is not None and timer_thread.is_alive():
            timer_thread.join()