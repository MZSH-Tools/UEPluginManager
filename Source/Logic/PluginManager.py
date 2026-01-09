# 插件管理业务逻辑
import json
from pathlib import Path
from typing import Optional
from Source.Data.PluginReader import PluginReader, PluginInfo, ProjectInfo, PluginSource


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.Reader: Optional[PluginReader] = None
        self.ProjectInfo: Optional[ProjectInfo] = None
        self.Plugins: list[PluginInfo] = []
        self._FilteredPlugins: list[PluginInfo] = []

    def LoadProject(self, ProjectPath: Path) -> bool:
        """加载项目"""
        self.Reader = PluginReader(ProjectPath)
        self.ProjectInfo = self.Reader.LoadProject()

        if not self.ProjectInfo:
            return False

        self.Plugins = self.Reader.LoadAllPlugins()
        self._FilteredPlugins = self.Plugins.copy()
        return True

    def GetPlugins(self, Source: Optional[PluginSource] = None) -> list[PluginInfo]:
        """获取插件列表"""
        if Source is None:
            return self._FilteredPlugins
        return [P for P in self._FilteredPlugins if P.Source == Source]

    def Search(self, Keyword: str) -> list[PluginInfo]:
        """搜索插件"""
        if not Keyword:
            self._FilteredPlugins = self.Plugins.copy()
        else:
            Keyword = Keyword.lower()
            self._FilteredPlugins = [
                P for P in self.Plugins
                if Keyword in P.Name.lower()
                or Keyword in P.Description.lower()
                or Keyword in P.Category.lower()
            ]
        return self._FilteredPlugins

    def Filter(self, Source: Optional[PluginSource] = None,
               Category: Optional[str] = None,
               EnabledOnly: Optional[bool] = None) -> list[PluginInfo]:
        """过滤插件"""
        Result = self.Plugins.copy()

        if Source is not None:
            Result = [P for P in Result if P.Source == Source]

        if Category:
            Result = [P for P in Result if P.Category == Category]

        if EnabledOnly is not None:
            if EnabledOnly:
                Result = [P for P in Result if P.EnabledInProject is True or
                          (P.EnabledInProject is None and P.EnabledByDefault)]
            else:
                Result = [P for P in Result if P.EnabledInProject is False or
                          (P.EnabledInProject is None and not P.EnabledByDefault)]

        self._FilteredPlugins = Result
        return Result

    def GetCategories(self) -> list[str]:
        """获取所有分类"""
        Categories = set()
        for Plugin in self.Plugins:
            if Plugin.Category:
                Categories.add(Plugin.Category)
        return sorted(list(Categories))

    def SetPluginEnabled(self, PluginName: str, Enabled: bool) -> bool:
        """设置插件启用状态"""
        if not self.ProjectInfo:
            return False

        # 更新内存中的状态
        for Plugin in self.Plugins:
            if Plugin.Name == PluginName:
                Plugin.EnabledInProject = Enabled
                break

        # 更新项目文件
        return self._UpdateProjectFile(PluginName, Enabled)

    def _UpdateProjectFile(self, PluginName: str, Enabled: bool) -> bool:
        """更新项目文件中的插件状态"""
        if not self.ProjectInfo:
            return False

        UProjectFile = list(self.ProjectInfo.Path.glob("*.uproject"))[0]

        try:
            with open(UProjectFile, "r", encoding="utf-8") as F:
                Data = json.load(F)

            Plugins = Data.get("Plugins", [])

            # 查找是否已存在
            Found = False
            for Plugin in Plugins:
                if Plugin.get("Name") == PluginName:
                    Plugin["Enabled"] = Enabled
                    Found = True
                    break

            if not Found:
                Plugins.append({"Name": PluginName, "Enabled": Enabled})
                Data["Plugins"] = Plugins

            with open(UProjectFile, "w", encoding="utf-8") as F:
                json.dump(Data, F, indent="\t", ensure_ascii=False)

            # 更新内存中的项目信息
            if Enabled:
                if PluginName in self.ProjectInfo.DisabledPlugins:
                    self.ProjectInfo.DisabledPlugins.remove(PluginName)
                if PluginName not in self.ProjectInfo.EnabledPlugins:
                    self.ProjectInfo.EnabledPlugins.append(PluginName)
            else:
                if PluginName in self.ProjectInfo.EnabledPlugins:
                    self.ProjectInfo.EnabledPlugins.remove(PluginName)
                if PluginName not in self.ProjectInfo.DisabledPlugins:
                    self.ProjectInfo.DisabledPlugins.append(PluginName)

            return True
        except Exception as E:
            print(f"更新项目文件失败: {E}")
            return False

    def GetDependencies(self, PluginName: str) -> list[str]:
        """获取插件依赖"""
        for Plugin in self.Plugins:
            if Plugin.Name == PluginName:
                return Plugin.Plugins
        return []

    def GetDependents(self, PluginName: str) -> list[str]:
        """获取依赖此插件的其他插件"""
        Dependents = []
        for Plugin in self.Plugins:
            if PluginName in Plugin.Plugins:
                Dependents.append(Plugin.Name)
        return Dependents

    def GetPluginByName(self, Name: str) -> Optional[PluginInfo]:
        """根据名称获取插件"""
        for Plugin in self.Plugins:
            if Plugin.Name == Name:
                return Plugin
        return None

    def GetStats(self) -> dict:
        """获取统计信息"""
        ProjectPlugins = [P for P in self.Plugins if P.Source == PluginSource.Project]
        EnginePlugins = [P for P in self.Plugins if P.Source == PluginSource.Engine]

        EnabledCount = sum(
            1 for P in self.Plugins
            if P.EnabledInProject is True or
            (P.EnabledInProject is None and P.EnabledByDefault)
        )

        return {
            "Total": len(self.Plugins),
            "Project": len(ProjectPlugins),
            "Engine": len(EnginePlugins),
            "Enabled": EnabledCount,
            "Disabled": len(self.Plugins) - EnabledCount
        }
