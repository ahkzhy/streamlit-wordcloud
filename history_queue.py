import pandas as pd
from collections import deque

class HistoryDataQueue:
    def __init__(self, max_length=10):
        self.queue = deque(maxlen=max_length)  # 队列：自动维护长度，超出时淘汰最早元素
        # 存储格式：(timestamp, freq_df)，其中freq_df是该时间点的词频DataFrame（含'word'和'frequency'列）

    def add(self, freq_df):
        """添加新的词频数据（自动记录时间戳，超出长度时淘汰最早的）"""
        timestamp = pd.Timestamp.now()  # 记录当前时间
        self.queue.append((timestamp, freq_df))

    def get_recent(self, n=2):
        """获取最近的n个时间点的词频数据（用于新旧对比）"""
        if len(self.queue) < n:
            return list(self.queue)  # 数据不足时返回所有
        return list(self.queue)[-n:]  # 取最后n个（最新的n个）

    def get_all(self):
        """获取所有保留的词频数据（按时间顺序，从早到晚）"""
        return list(self.queue)

    def get_oldest(self):
        """获取最早的词频数据"""
        return self.queue[0] if self.queue else None

    def get_latest(self):
        """获取最新的词频数据"""
        return self.queue[-1] if self.queue else None

    def size(self):
        """获取当前队列大小"""
        return len(self.queue)
