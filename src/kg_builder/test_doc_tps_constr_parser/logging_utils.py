import time
from datetime import datetime


class StepLogger:
    """简单的步骤日志工具，跟踪程序执行流程"""

    def __init__(self, enable=True, show_time=True):
        self.enable = enable
        self.show_time = show_time
        self.step_counter = 0
        self.start_time = time.time()
        self.last_step_time = self.start_time

        if enable:
            self.log(f"=== 程序开始执行 === {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def log(self, message, is_step=False):
        """记录一条日志消息"""
        if not self.enable:
            return

        current_time = time.time()
        elapsed = current_time - self.start_time
        step_elapsed = current_time - self.last_step_time

        if is_step:
            self.step_counter += 1
            prefix = f"[步骤 {self.step_counter}]"
            self.last_step_time = current_time
        else:
            prefix = "    >"

        time_info = ""
        if self.show_time:
            time_info = f" (总用时: {elapsed:.2f}s"
            if is_step and self.step_counter > 1:
                time_info += f", 步骤用时: {step_elapsed:.2f}s"
            time_info += ")"

        print(f"{prefix} {message}{time_info}")

    def step(self, message):
        """记录一个主要步骤"""
        self.log(message, is_step=True)

    def finish(self):
        """记录程序结束"""
        if self.enable:
            total_time = time.time() - self.start_time
            self.log(f"=== 程序执行完成 === 总用时: {total_time:.2f}秒", is_step=False)