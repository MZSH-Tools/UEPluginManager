# 插件管理业务逻辑
import json
import os
import stat
from pathlib import Path
from typing import Optional
from Source.Data.PluginReader import PluginReader, PluginInfo, ProjectInfo, PluginSource


def RemoveReadOnly(Path: Path):
    """递归移除目录及其内容的只读属性"""
    if Path.is_file():
        os.chmod(Path, stat.S_IWRITE)
    elif Path.is_dir():
        for Item in Path.rglob("*"):
            if Item.is_file():
                os.chmod(Item, stat.S_IWRITE)


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
                        Dependents = [Name for Name, _ in self.GetAllDependents(P.Name)]
                        Match = any(Keyword in Dep.lower() for Dep in Dependents)
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

        # 先更新项目文件，成功后再更新内存
        if not self.UpdateProjectFile(PluginName, Enabled):
            return False

        # 更新内存中的状态
        for Plugin in self.Plugins[Source]:
            if Plugin.Name == PluginName:
                Plugin.EnabledInProject = Enabled
                break

        return True

    def UpdateProjectFile(self, PluginName: str, Enabled: bool) -> bool:
        """更新项目文件中的插件状态"""
        if not self.ProjectInfo:
            return False

        UProjectFiles = list(self.ProjectInfo.Path.glob("*.uproject"))
        if not UProjectFiles:
            return False
        UProjectFile = UProjectFiles[0]

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

    def ResetPluginToDefault(self, PluginName: str, Source: PluginSource) -> bool:
        """恢复插件到默认状态（从项目文件中移除配置）"""
        if not self.ProjectInfo:
            return False

        UProjectFiles = list(self.ProjectInfo.Path.glob("*.uproject"))
        if not UProjectFiles:
            return False
        UProjectFile = UProjectFiles[0]

        try:
            with open(UProjectFile, "r", encoding="utf-8") as F:
                Data = json.load(F)

            Plugins = Data.get("Plugins", [])

            # 移除插件配置
            Data["Plugins"] = [P for P in Plugins if P.get("Name") != PluginName]

            with open(UProjectFile, "w", encoding="utf-8") as F:
                json.dump(Data, F, indent="\t", ensure_ascii=False)

            # 更新内存中的状态
            if PluginName in self.ProjectInfo.EnabledPlugins:
                self.ProjectInfo.EnabledPlugins.remove(PluginName)
            if PluginName in self.ProjectInfo.DisabledPlugins:
                self.ProjectInfo.DisabledPlugins.remove(PluginName)

            for Plugin in self.Plugins[Source]:
                if Plugin.Name == PluginName:
                    Plugin.EnabledInProject = None
                    break

            return True
        except Exception as E:
            print(f"恢复默认状态失败: {E}")
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

    def GetConflictingPlugin(self, Name: str, Source: PluginSource) -> Optional[tuple[PluginInfo, PluginSource]]:
        """获取同名冲突插件（返回另一个来源的同名插件）"""
        for S in PluginSource:
            if S == Source:
                continue
            for Plugin in self.Plugins[S]:
                if Plugin.Name == Name:
                    return (Plugin, S)
        return None

    def HasConflict(self, Name: str) -> bool:
        """检查插件是否存在同名冲突"""
        FoundSources = []
        for S in PluginSource:
            for Plugin in self.Plugins[S]:
                if Plugin.Name == Name:
                    FoundSources.append(S)
                    break
        return len(FoundSources) > 1

    def RenamePluginFolder(self, Name: str, Source: PluginSource) -> tuple[bool, str]:
        """重命名插件文件夹为插件同名，返回 (成功, 错误信息)"""
        Plugin = self.GetPluginByName(Name, Source)
        if not Plugin:
            return False, "插件不存在"

        OldPath = Plugin.Path
        NewPath = OldPath.parent / Name

        # 已经是正确名称
        if OldPath.name == Name:
            return True, ""

        # 目标路径已存在
        if NewPath.exists():
            return False, f"目标路径已存在: {NewPath}"

        try:
            RemoveReadOnly(OldPath)
            OldPath.rename(NewPath)
            Plugin.Path = NewPath
            return True, ""
        except PermissionError:
            return False, "拒绝访问，请确保 UE 编辑器已关闭。\n如果重试后仍失败，请手动执行。"
        except Exception as E:
            return False, str(E)

    def DeletePlugin(self, Name: str, Source: PluginSource) -> tuple[bool, str]:
        """删除插件（移动到回收站），返回 (成功, 错误信息)"""
        import shutil
        Plugin = self.GetPluginByName(Name, Source)
        if not Plugin:
            return False, "插件不存在"

        try:
            RemoveReadOnly(Plugin.Path)
            # 使用 send2trash 移动到回收站（如果可用）
            try:
                from send2trash import send2trash
                send2trash(str(Plugin.Path))
            except ImportError:
                # 没有 send2trash，直接删除
                shutil.rmtree(Plugin.Path)

            # 从内存中移除
            self.Plugins[Source] = [P for P in self.Plugins[Source] if P.Name != Name]
            self.FilteredPlugins[Source] = [P for P in self.FilteredPlugins[Source] if P.Name != Name]

            # 从项目文件移除配置
            self.ResetPluginToDefault(Name, Source)

            return True, ""
        except PermissionError:
            return False, "拒绝访问，请确保 UE 编辑器已关闭。\n如果重试后仍失败，请手动执行。"
        except Exception as E:
            return False, str(E)

    def MovePlugin(self, Name: str, FromSource: PluginSource, ToSource: PluginSource) -> tuple[bool, str]:
        """移动插件到另一个来源目录，返回 (成功, 错误信息)"""
        import shutil
        Plugin = self.GetPluginByName(Name, FromSource)
        if not Plugin:
            return False, "插件不存在"

        # 确定目标目录
        if ToSource == PluginSource.Project:
            TargetDir = self.ProjectInfo.Path / "Plugins"
        elif ToSource == PluginSource.Fab:
            if not self.ProjectInfo.EnginePath:
                return False, "未找到引擎路径，无法移动到商城目录"
            TargetDir = self.ProjectInfo.EnginePath / "Engine" / "Plugins" / "Marketplace"
        else:
            return False, "不支持的目标位置"

        # 确保目标目录存在
        TargetDir.mkdir(parents=True, exist_ok=True)
        NewPath = TargetDir / Plugin.Path.name

        # 目标已存在
        if NewPath.exists():
            return False, f"目标路径已存在: {NewPath}"

        try:
            RemoveReadOnly(Plugin.Path)
            shutil.move(str(Plugin.Path), str(NewPath))

            # 更新内存中的数据
            self.Plugins[FromSource] = [P for P in self.Plugins[FromSource] if P.Name != Name]
            self.FilteredPlugins[FromSource] = [P for P in self.FilteredPlugins[FromSource] if P.Name != Name]

            Plugin.Path = NewPath
            Plugin.Source = ToSource
            self.Plugins[ToSource].append(Plugin)
            self.FilteredPlugins[ToSource].append(Plugin)

            return True, ""
        except PermissionError:
            # 跨盘符移动时可能已复制部分文件，需要清理
            if NewPath.exists():
                try:
                    shutil.rmtree(NewPath)
                except Exception:
                    pass
            return False, "拒绝访问，请确保 UE 编辑器已关闭。\n如果重试后仍失败，请手动执行。"
        except Exception as E:
            # 清理可能已复制的文件
            if NewPath.exists():
                try:
                    shutil.rmtree(NewPath)
                except Exception:
                    pass
            return False, str(E)

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
