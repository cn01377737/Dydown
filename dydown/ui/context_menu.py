import typing
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

class ContextMenu:
    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.operations = {
            'retry': self._handle_retry,
            'pause': self._handle_pause,
            'cancel': self._handle_cancel,
            'priority': self._handle_priority
        }

    def _handle_retry(self, task_id):
        '''处理任务重试操作'''
        self.task_manager.retry_task(task_id)
        
    def _handle_pause(self, task_id):
        '''处理任务暂停/恢复操作'''
        self.task_manager.toggle_task_pause(task_id)

    def _handle_cancel(self, task_id):
        '''处理任务取消操作'''
        self.task_manager.cancel_task(task_id)

    def _handle_priority(self, task_id, level):
        '''处理任务优先级调整'''
        self.task_manager.set_task_priority(task_id, level)

    def render_menu(self, task_id) -> Table:
        '''生成带状态标记的上下文菜单'''
        menu = Table.grid(padding=(0,1))
        menu.add_row("[1] 立即重试", self._get_badge('retry'))
        menu.add_row("[2] 暂停/恢复", self._get_badge('pause'))
        menu.add_row("[3] 取消任务", self._get_badge('cancel'))
        menu.add_row("[4] 设置优先级", self._get_priority_menu(task_id))
        return Panel(menu, title="任务操作")

    def _get_badge(self, op_type) -> Text:
        '''生成带状态标记的操作徽章'''
        status = self.task_manager.get_op_status(op_type)
        return Text(f"{op_type.upper()} {status}", style="yellow" if status else "green")

    def _get_priority_menu(self, task_id) -> Table:
        '''生成优先级子菜单'''
        submenu = Table.grid()
        for level in ['low', 'normal', 'high']:
            submenu.add_row(f"> {level}", self._get_priority_badge(task_id, level))
        return submenu

    def _get_priority_badge(self, task_id, level) -> Text:
        '''生成带选中状态的优先级标记'''
        current_level = self.task_manager.get_task_priority(task_id)
        return Text("◉" if level == current_level else "○", style="blue")