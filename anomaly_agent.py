from typing import List
import re

class AnomalyAgent:
    def __init__(self, keywords=None):
        if keywords is None:
            keywords = ["UP", "timeout", "reset", "down", "fail", "alarm", "unreachable", "reject", "error"]
        self.keywords = [k.lower() for k in keywords]

    def detect(self, logs: str) -> List[str]:
        suspicious_lines = []
        for line in logs.splitlines():
            if any(k in line.lower() for k in self.keywords):
                suspicious_lines.append(line.strip())
        return suspicious_lines
