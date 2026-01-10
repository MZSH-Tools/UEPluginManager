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
        self.Plugins: dict[PluginSource, list[PluginInfo]] = {
            PluginSource.Project: [],
            PluginSource.Engine: [],
            PluginSource.Fab: []
        }
        self.FilteredPlugins: dict[PluginSource, list[PluginInfo]] = {
            PluginSource.Project: [],
            PluginSource.Engine: [],
            PluginSource.Fab: []
        }

    def LoadProject(self, ProjectPath: Path) -> bool:
        """加载项目"""
        self.Reader = PluginReader(ProjectPath)
        self.ProjectInfo = self.Reader.LoadProject()

        if not self.ProjectInfo:
            return False

        self.Plugins = self.Reader.LoadAllPlugins()
        for Source in PluginSource:
            self.FilteredPlugins[Source] = self.Plugins[Source].copy()
        return True

    def GetPlugins(self, Source: PluginSource) -> list[PluginInfo]:
        """获取指定来源的插件列表"""
        return self.FilteredPlugins[Source]

    def Search(self, Keyword: str, Field: int = 0):
        """搜索插件，Field: 0名称 1作者 2分类 3描述 4依赖 5被依赖"""
        if not Keyword:
            for Source in PluginSource:
                self.FilteredPlugins[Source] = self.Plugins[Source].copy()
        else:
            Keyword = Keyword.lower()
            for Source in PluginSource:
                self.FilteredPlugins[Source] = []
                for P in self.Plugins[Source]:
                    Match = False
                    if Field == 0:
                        Match = Keyword in P.Name.lower()
                    elif Field == 1:
                        Match = Keyword in P.CreatedBy.lower()
                    elif Field == 2:
                        Match = Keyword in P.Category.lower()
                    elif Field == 3:
                        Match = Keyword in P.Description.lower()
                    elif Field == 4:
                        Match = any(Keyword in Dep.lower() for Dep in P.Plugins)
                    elif Field == 5:
                        Match = any(Keyword in Dep.lower() for Dep in self.GetDependents(P.Name, Source))
                    if Match:
                        self.FilteredPlugins[Source].append(P)

    def GetCategories(self, Source: PluginSource) -> list[str]:
        """获取指定来源的所有分类"""
        Categories = set()
        for Plugin in self.Plugins[Source]:
            if Plugin.Category:
                Categories.add(Plugin.Category)
        return sorted(list(Categories))

    def SetPluginEnabled(self, PluginName: str, Source: PluginSource, Enabled: bool) -> bool:
        """设置插件启用状态"""
        if not self.ProjectInfo:
            return False

        # 更新内存中的状态
        for Plugin in self.Plugins[Source]:
            if Plugin.Name == PluginName:
                Plugin.EnabledInProject = Enabled
                break

        # 更新项目文件
        return self.UpdateProjectFile(PluginName, Enabled)

    def UpdateProjectFile(self, PluginName: str, Enabled: bool) -> bool:
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

    def GetDependencies(self, PluginName: str, Source: PluginSource) -> list[str]:
        """获取插件依赖"""
        for Plugin in self.Plugins[Source]:
            if Plugin.Name == PluginName:
                return Plugin.Plugins
        return []

    def GetDependents(self, PluginName: str, Source: PluginSource) -> list[str]:
        """获取依赖此插件的其他插件（在同一来源中）"""
        Dependents = []
        for Plugin in self.Plugins[Source]:
            if PluginName in Plugin.Plugins:
                Dependents.append(Plugin.Name)
        return Dependents

    def GetAllDependents(self, PluginName: str) -> list[tuple[str, PluginSource]]:
        """获取所有来源中依赖此插件的插件列表"""
        Dependents = []
        for Source in PluginSource:
            for Plugin in self.Plugins[Source]:
                if PluginName in Plugin.Plugins:
                    Dependents.append((Plugin.Name, Source))
        return Dependents

    def GetAllDependencies(self, PluginName: str, Source: PluginSource) -> list[tuple[str, PluginSource]]:
        """获取插件的所有依赖（跨来源查找）"""
        Plugin = self.GetPluginByName(PluginName, Source)
        if not Plugin:
            return []

        Dependencies = []
        for DepName in Plugin.Plugins:
            for S in PluginSource:
                DepPlugin = self.GetPluginByName(DepName, S)
                if DepPlugin:
                    Dependencies.append((DepName, S))
                    break
        return Dependencies

    def IsPluginEnabled(self, PluginName: str, Source: PluginSource) -> bool:
        """检查插件是否启用"""
        Plugin = self.GetPluginByName(PluginName, Source)
        if not Plugin:
            return False
        if Plugin.EnabledInProject is True:
            return True
        if Plugin.EnabledInProject is False:
            return False
        return Plugin.EnabledByDefault

    def GetDisabledDependents(self, PluginName: str) -> list[tuple[str, PluginSource]]:
        """获取所有依赖此插件且当前启用的插件（禁用时需连带禁用）"""
        Result = []
        for Name, Source in self.GetAllDependents(PluginName):
            if self.IsPluginEnabled(Name, Source):
                Result.append((Name, Source))
        return Result

    def GetDisabledDependencies(self, PluginName: str, Source: PluginSource) -> list[tuple[str, PluginSource]]:
        """获取插件依赖中当前未启用的插件（启用时需连带启用）"""
        Result = []
        for DepName, DepSource in self.GetAllDependencies(PluginName, Source):
            if not self.IsPluginEnabled(DepName, DepSource):
                Result.append((DepName, DepSource))
        return Result

    def GetPluginByName(self, Name: str, Source: PluginSource) -> Optional[PluginInfo]:
        """根据名称和来源获取插件"""
        for Plugin in self.Plugins[Source]:
            if Plugin.Name == Name:
                return Plugin
        return None

    def GetStats(self) -> dict:
        """获取统计信息"""
        Total = sum(len(self.Plugins[S]) for S in PluginSource)
        EnabledCount = 0
        for Source in PluginSource:
            for P in self.Plugins[Source]:
                if P.EnabledInProject is True or (P.EnabledInProject is None and P.EnabledByDefault):
                    EnabledCount += 1

        return {
            "Total": Total,
            "Project": len(self.Plugins[PluginSource.Project]),
            "Engine": len(self.Plugins[PluginSource.Engine]),
            "Fab": len(self.Plugins[PluginSource.Fab]),
            "Enabled": EnabledCount,
            "Disabled": Total - EnabledCount
        }
