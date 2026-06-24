from enum import Enum

class WorkMode(Enum):
    CHAT = "chat"
    SYSTEM_ADMIN = "system_admin"
    QUANT_DEV = "quant_dev"
    QUANT_TRAIN = "quant_train"

class IntentClassifier:
    """意图分类器：基于关键词的简单规则版本，后续可替换为模型"""
    
    @staticmethod
    def classify(text: str) -> WorkMode:
        text_lower = text.lower()
        
        # 系统管理关键词
        sys_keywords = ["注册表", "服务", "系统", "权限", "管理", "驱动", "磁盘", "清理", "进程"]
        if any(kw in text_lower for kw in sys_keywords):
            return WorkMode.SYSTEM_ADMIN
        
        # 量化训练关键词
        train_keywords = ["训练", "epoch", "过拟合", "模型保存", "loss", "梯度"]
        if any(kw in text_lower for kw in train_keywords):
            return WorkMode.QUANT_TRAIN
        
        # 量化开发关键词
        quant_keywords = ["回测", "因子", "均线", "仓位", "止损", "止盈", "k线", "行情", "策略", "ticker"]
        if any(kw in text_lower for kw in quant_keywords):
            return WorkMode.QUANT_DEV
        
        return WorkMode.CHAT