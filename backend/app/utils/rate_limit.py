"""
简单的登录限流和失败冷却机制
使用内存存储，生产环境可替换为Redis
"""
import time
from typing import Dict, Tuple
from datetime import datetime, timedelta

class LoginRateLimiter:
    """登录限流器"""
    
    def __init__(self):
        # 存储格式：{email: (失败次数, 最后失败时间, 冷却到期时间)}
        self._failed_attempts: Dict[str, Tuple[int, float, float]] = {}
        self.max_attempts = 5  # 最大失败次数
        self.cooldown_seconds = 300  # 冷却时间5分钟
        self.attempt_window = 900  # 失败次数统计窗口15分钟
    
    def is_blocked(self, email: str) -> Tuple[bool, int]:
        """
        检查账号是否被冷却
        
        返回：
        - (是否被冷却, 剩余冷却秒数)
        """
        if email not in self._failed_attempts:
            return False, 0
        
        attempts, last_fail_time, cooldown_end = self._failed_attempts[email]
        current_time = time.time()
        
        # 如果在冷却期内
        if current_time < cooldown_end:
            remaining = int(cooldown_end - current_time)
            return True, remaining
        
        # 冷却期已过，清理记录
        if current_time >= cooldown_end:
            del self._failed_attempts[email]
            return False, 0
        
        return False, 0
    
    def record_failure(self, email: str):
        """记录登录失败"""
        current_time = time.time()
        
        if email in self._failed_attempts:
            attempts, last_fail_time, _ = self._failed_attempts[email]
            
            # 如果距离上次失败超过统计窗口，重置计数
            if current_time - last_fail_time > self.attempt_window:
                attempts = 0
            
            attempts += 1
            
            # 如果达到最大失败次数，设置冷却
            if attempts >= self.max_attempts:
                cooldown_end = current_time + self.cooldown_seconds
            else:
                cooldown_end = 0
            
            self._failed_attempts[email] = (attempts, current_time, cooldown_end)
        else:
            # 首次失败
            self._failed_attempts[email] = (1, current_time, 0)
    
    def record_success(self, email: str):
        """记录登录成功，清除失败记录"""
        if email in self._failed_attempts:
            del self._failed_attempts[email]
    
    def cleanup_expired(self):
        """清理过期记录（可定期调用）"""
        current_time = time.time()
        expired_emails = [
            email for email, (_, last_fail, cooldown_end) in self._failed_attempts.items()
            if current_time - last_fail > self.attempt_window and current_time >= cooldown_end
        ]
        for email in expired_emails:
            del self._failed_attempts[email]

# 全局限流器实例
login_limiter = LoginRateLimiter()
