# 插件数据读取模块
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class PluginSource(Enum):
    """插件来源"""
    Project = "Project"  # 项目插件
    Engine = "Engine"    # 引擎插件
    Fab = "Fab"          # Fab 商城插件


@dataclass
class PluginInfo:
    """插件信息"""
    Name: str
    Path: Path
    Source: PluginSource
    Version: str = ""
    Description: str = ""
    Category: str = ""
    CreatedBy: str = ""
    DocsURL: str = ""
    EnabledByDefault: bool = False
    CanContainContent: bool = False
    IsBetaVersion: bool = False
    Modules: list = field(default_factory=list)
    Plugins: list = field(default_factory=list)  # 依赖的插件

    # 项目中的启用状态（仅对引擎插件有效）
    EnabledInProject: Optional[bool] = None


@dataclass
class ProjectInfo:
    """项目信息"""
    Name: str
    Path: Path
    EngineVersion: str
    EnginePath: Optional[Path] = None
    EnabledPlugins: list = field(default_factory=list)
    DisabledPlugins: list = field(default_factory=list)


class PluginReader:
    """插件读取器"""

    def __init__(self, ProjectPath: Path):
        self.ProjectPath = ProjectPath
        self.ProjectInfo: Optional[ProjectInfo] = None
        self.Plugins: dict[PluginSource, list[PluginInfo]] = {
            PluginSource.Project: [],
            PluginSource.Engine: [],
            PluginSource.Fab: []
        }

    def LoadProject(self) -> Optional[ProjectInfo]:
        """加载项目信息"""
        UProjectFiles = list(self.ProjectPath.glob("*.uproject"))
        if not UProjectFiles:
            return None

        UProjectFile = UProjectFiles[0]
        try:
            with open(UProjectFile, "r", encoding="utf-8-sig") as F:
                Data = json.load(F)
        except (json.JSONDecodeError, IOError) as E:
            print(f"加载项目文件失败: {UProjectFile} - {E}")
            return None

        # 解析引擎版本
        EngineAssociation = Data.get("EngineAssociation", "")

        # 解析插件启用状态
        EnabledPlugins = []
        DisabledPlugins = []
        for Plugin in Data.get("Plugins", []):
            PluginName = Plugin.get("Name", "")
            if Plugin.get("Enabled", True):
                EnabledPlugins.append(PluginName)
            else:
                DisabledPlugins.append(PluginName)

        self.ProjectInfo = ProjectInfo(
            Name=UProjectFile.stem,
            Path=self.ProjectPath,
            EngineVersion=EngineAssociation,
            EnginePath=self.FindEnginePath(EngineAssociation),
            EnabledPlugins=EnabledPlugins,
            DisabledPlugins=DisabledPlugins
        )
        return self.ProjectInfo

    def FindEnginePath(self, EngineVersion: str) -> Optional[Path]:
        """查找引擎路径"""
        if not EngineVersion:
            return None

        # 检查是否是 GUID（源码版本）
        if len(EngineVersion) == 32 or "-" in EngineVersion:
            return self.FindEngineByGUID(EngineVersion)

        # 标准版本号，查找安装路径
        return self.FindEngineByVersion(EngineVersion)

    def FindEngineByGUID(self, GUID: str) -> Optional[Path]:
        """通过 GUID 查找源码版引擎"""
        # Windows 注册表路径
        import winreg
        try:
            Key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Epic Games\Unreal Engine\Builds"
            )
            EnginePath, _ = winreg.QueryValueEx(Key, GUID)
            winreg.CloseKey(Key)
            return Path(EnginePath)
        except (OSError, FileNotFoundError):
            return None

    def FindEngineByVersion(self, Version: str) -> Optional[Path]:
        """通过版本号查找安装版引擎"""
        import winreg
        try:
            Key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                rf"SOFTWARE\EpicGames\Unreal Engine\{Version}"
            )
            InstallDir, _ = winreg.QueryValueEx(Key, "InstalledDirectory")
            winreg.CloseKey(Key)
            return Path(InstallDir)
        except (OSError, FileNotFoundError):
            # 尝试默认路径
            DefaultPath = Path(f"C:/Program Files/Epic Games/UE_{Version}")
            if DefaultPath.exists():
                return DefaultPath
            return None

    def LoadAllPlugins(self) -> dict[PluginSource, list[PluginInfo]]:
        """加载所有插件"""
        for Source in PluginSource:
            self.Plugins[Source].clear()

        if not self.ProjectInfo:
            self.LoadProject()

        if not self.ProjectInfo:
            return self.Plugins

        # 加载项目插件
        self.LoadPluginsFromDir(
            self.ProjectPath / "Plugins",
            PluginSource.Project
        )

        # 加载引擎插件
        if self.ProjectInfo.EnginePath:
            self.LoadPluginsFromDir(
                self.ProjectInfo.EnginePath / "Engine" / "Plugins",
                PluginSource.Engine
            )

        # 更新启用状态
        self.UpdateEnabledStatus()

        return self.Plugins

    def LoadPluginsFromDir(self, PluginsDir: Path, Source: PluginSource):
        """从目录加载插件"""
        if not PluginsDir.exists():
            return

        for UPluginFile in PluginsDir.rglob("*.uplugin"):
            Plugin = self.ParsePluginFile(UPluginFile, Source)
            if Plugin:
                self.Plugins[Plugin.Source].append(Plugin)

    def ParsePluginFile(self, UPluginFile: Path, Source: PluginSource) -> Optional[PluginInfo]:
        """解析插件文件"""
        try:
            with open(UPluginFile, "r", encoding="utf-8-sig") as F:
                Content = F.read()
            # 去除尾随逗号（UE 的 JSON 允许尾随逗号，标准 JSON 不允许）
            Content = re.sub(r',(\s*[\]\}])', r'\1', Content)
            Data = json.loads(Content)

            # 解析依赖插件
            Dependencies = []
            for Plugin in Data.get("Plugins", []):
                if Plugin.get("Enabled", True):
                    Dependencies.append(Plugin.get("Name", ""))

            # 检测是否为 Fab 商城插件
            ActualSource = Source
            if "Marketplace" in UPluginFile.parts:
                ActualSource = PluginSource.Fab

            return PluginInfo(
                Name=UPluginFile.stem,
                Path=UPluginFile.parent,
                Source=ActualSource,
                Version=str(Data.get("Version", Data.get("VersionName", ""))),
                Description=Data.get("Description", ""),
                Category=Data.get("Category", ""),
                CreatedBy=Data.get("CreatedBy", ""),
                DocsURL=Data.get("DocsURL", ""),
                EnabledByDefault=Data.get("EnabledByDefault", False),
                CanContainContent=Data.get("CanContainContent", False),
                IsBetaVersion=Data.get("IsBetaVersion", False),
                Modules=Data.get("Modules", []),
                Plugins=Dependencies
            )
        except Exception as E:
            print(f"解析插件失败: {UPluginFile} - {E}")
            return None

    def UpdateEnabledStatus(self):
        """更新插件在项目中的启用状态"""
        if not self.ProjectInfo:
            return

        for Source in PluginSource:
            for Plugin in self.Plugins[Source]:
                if Plugin.Name in self.ProjectInfo.EnabledPlugins:
                    Plugin.EnabledInProject = True
                elif Plugin.Name in self.ProjectInfo.DisabledPlugins:
                    Plugin.EnabledInProject = False
                else:
                    Plugin.EnabledInProject = None  # 未显式配置
