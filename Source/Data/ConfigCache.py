# 配置缓存模块
import json
from pathlib import Path
from platformdirs import user_cache_dir


class ConfigCache:
    """配置缓存管理"""

    def __init__(self):
        self.CacheDir = Path(user_cache_dir("UEPluginManager", "MZSH"))
        self.CacheDir.mkdir(parents=True, exist_ok=True)
        self.ConfigFile = self.CacheDir / "config.json"
        self._Config = self._Load()

    def _Load(self) -> dict:
        """加载配置"""
        if self.ConfigFile.exists():
            try:
                with open(self.ConfigFile, "r", encoding="utf-8") as F:
                    return json.load(F)
            except:
                pass
        return self._GetDefaults()

    def _GetDefaults(self) -> dict:
        """默认配置"""
        return {
            "SearchField": 0
        }

    def _Save(self):
        """保存配置"""
        with open(self.ConfigFile, "w", encoding="utf-8") as F:
            json.dump(self._Config, F, indent="\t", ensure_ascii=False)

    def Get(self, Key: str, Default=None):
        """获取配置值"""
        return self._Config.get(Key, Default)

    def Set(self, Key: str, Value):
        """设置配置值"""
        self._Config[Key] = Value
        self._Save()
