# 主窗口
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QLabel, QTextEdit,
    QGroupBox, QCheckBox, QPushButton, QMessageBox, QHeaderView, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from Source.Logic.PluginManager import PluginManager
from Source.Data.PluginReader import PluginInfo, PluginSource


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.Manager = PluginManager()
        self._InitUI()
        self._LoadProject(Path.cwd())

    def _InitUI(self):
        """初始化界面"""
        self.setWindowTitle("UE Plugin Manager")
        self.setMinimumSize(1200, 700)

        # 中心控件
        CentralWidget = QWidget()
        self.setCentralWidget(CentralWidget)
        MainLayout = QVBoxLayout(CentralWidget)

        # 顶部工具栏
        ToolBar = self._CreateToolBar()
        MainLayout.addLayout(ToolBar)

        # 主内容区（左右分栏）
        Splitter = QSplitter(Qt.Horizontal)

        # 左侧：插件列表
        LeftPanel = self._CreatePluginList()
        Splitter.addWidget(LeftPanel)

        # 右侧：详情面板
        RightPanel = self._CreateDetailPanel()
        Splitter.addWidget(RightPanel)

        Splitter.setSizes([600, 400])
        MainLayout.addWidget(Splitter)

        # 状态栏
        self.StatusBar = QStatusBar()
        self.setStatusBar(self.StatusBar)

    def _CreateToolBar(self) -> QHBoxLayout:
        """创建工具栏"""
        Layout = QHBoxLayout()

        # 项目目录
        Layout.addWidget(QLabel("项目:"))
        self.ProjectPathLabel = QLabel()
        self.ProjectPathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        Layout.addWidget(self.ProjectPathLabel, 1)
        self.OpenProjectBtn = QPushButton("打开")
        self.OpenProjectBtn.setFixedWidth(50)
        self.OpenProjectBtn.clicked.connect(self._OnOpenProjectFolder)
        Layout.addWidget(self.OpenProjectBtn)

        Layout.addSpacing(10)

        # 引擎目录
        Layout.addWidget(QLabel("引擎:"))
        self.EnginePathLabel = QLabel()
        self.EnginePathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        Layout.addWidget(self.EnginePathLabel, 1)
        self.OpenEngineBtn = QPushButton("打开")
        self.OpenEngineBtn.setFixedWidth(50)
        self.OpenEngineBtn.clicked.connect(self._OnOpenEngineFolder)
        Layout.addWidget(self.OpenEngineBtn)

        return Layout

    def _CreatePluginList(self) -> QWidget:
        """创建插件列表"""
        GroupBox = QGroupBox("插件列表")
        Layout = QVBoxLayout(GroupBox)

        # 搜索框
        self.SearchEdit = QLineEdit()
        self.SearchEdit.setPlaceholderText("搜索插件...")
        self.SearchEdit.textChanged.connect(self._OnSearch)
        Layout.addWidget(self.SearchEdit)

        self.PluginTree = QTreeWidget()
        self.PluginTree.setHeaderLabels(["名称", "来源", "分类", "状态"])
        self.PluginTree.setRootIsDecorated(False)
        self.PluginTree.setAlternatingRowColors(True)
        self.PluginTree.itemSelectionChanged.connect(self._OnPluginSelected)

        Header = self.PluginTree.header()
        Header.setSectionResizeMode(0, QHeaderView.Stretch)
        Header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        Header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        Header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        Layout.addWidget(self.PluginTree)

        return GroupBox

    def _CreateDetailPanel(self) -> QWidget:
        """创建详情面板"""
        GroupBox = QGroupBox("插件详情")
        Layout = QVBoxLayout(GroupBox)

        # 基本信息
        InfoLayout = QVBoxLayout()

        self.NameLabel = QLabel("名称: -")
        self.NameLabel.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        InfoLayout.addWidget(self.NameLabel)

        self.PathLabel = QLabel("路径: -")
        self.PathLabel.setWordWrap(True)
        InfoLayout.addWidget(self.PathLabel)

        self.VersionLabel = QLabel("版本: -")
        InfoLayout.addWidget(self.VersionLabel)

        self.AuthorLabel = QLabel("作者: -")
        InfoLayout.addWidget(self.AuthorLabel)

        self.CategoryLabel = QLabel("分类: -")
        InfoLayout.addWidget(self.CategoryLabel)

        Layout.addLayout(InfoLayout)

        # 描述
        Layout.addWidget(QLabel("描述:"))
        self.DescriptionEdit = QTextEdit()
        self.DescriptionEdit.setReadOnly(True)
        self.DescriptionEdit.setMaximumHeight(80)
        Layout.addWidget(self.DescriptionEdit)

        # 依赖
        Layout.addWidget(QLabel("依赖插件:"))
        self.DependenciesEdit = QTextEdit()
        self.DependenciesEdit.setReadOnly(True)
        self.DependenciesEdit.setMaximumHeight(60)
        Layout.addWidget(self.DependenciesEdit)

        # 被依赖
        Layout.addWidget(QLabel("被以下插件依赖:"))
        self.DependentsEdit = QTextEdit()
        self.DependentsEdit.setReadOnly(True)
        self.DependentsEdit.setMaximumHeight(60)
        Layout.addWidget(self.DependentsEdit)

        # 启用控制
        ControlLayout = QHBoxLayout()
        self.EnabledCheck = QCheckBox("在项目中启用")
        self.EnabledCheck.stateChanged.connect(self._OnEnabledChanged)
        ControlLayout.addWidget(self.EnabledCheck)

        self.OpenFolderBtn = QPushButton("打开目录")
        self.OpenFolderBtn.clicked.connect(self._OnOpenFolder)
        ControlLayout.addWidget(self.OpenFolderBtn)

        ControlLayout.addStretch()
        Layout.addLayout(ControlLayout)

        Layout.addStretch()

        return GroupBox

    def _LoadProject(self, ProjectPath: Path):
        """加载项目"""
        if not self.Manager.LoadProject(ProjectPath):
            return

        self.ProjectPathLabel.setText(str(ProjectPath))

        # 显示引擎路径
        Info = self.Manager.ProjectInfo
        if Info and Info.EnginePath:
            self.EnginePathLabel.setText(f"{Info.EngineVersion} ({Info.EnginePath})")
        elif Info:
            self.EnginePathLabel.setText(f"{Info.EngineVersion} (未找到)")
        else:
            self.EnginePathLabel.setText("-")

        # 刷新列表
        self._RefreshPluginList()

        # 更新状态栏
        Stats = self.Manager.GetStats()
        self.StatusBar.showMessage(
            f"共 {Stats['Total']} 个插件 | "
            f"项目: {Stats['Project']} | 引擎: {Stats['Engine']} | "
            f"已启用: {Stats['Enabled']} | 已禁用: {Stats['Disabled']}"
        )

    def _RefreshPluginList(self):
        """刷新插件列表"""
        self.PluginTree.clear()

        Plugins = self.Manager.GetPlugins()
        for Plugin in Plugins:
            Item = QTreeWidgetItem()
            Item.setText(0, Plugin.Name)
            Item.setText(1, "项目" if Plugin.Source == PluginSource.Project else "引擎")
            Item.setText(2, Plugin.Category or "-")

            # 状态
            if Plugin.EnabledInProject is True:
                Status = "启用"
            elif Plugin.EnabledInProject is False:
                Status = "禁用"
            else:
                Status = "默认" + ("(启用)" if Plugin.EnabledByDefault else "(禁用)")
            Item.setText(3, Status)

            Item.setData(0, Qt.UserRole, Plugin.Name)
            self.PluginTree.addTopLevelItem(Item)

    def _OnSearch(self, Text: str):
        """搜索"""
        self.Manager.Search(Text)
        self._RefreshPluginList()

    def _OnPluginSelected(self):
        """插件选中"""
        Items = self.PluginTree.selectedItems()
        if not Items:
            return

        PluginName = Items[0].data(0, Qt.UserRole)
        Plugin = self.Manager.GetPluginByName(PluginName)
        if not Plugin:
            return

        self._ShowPluginDetail(Plugin)

    def _ShowPluginDetail(self, Plugin: PluginInfo):
        """显示插件详情"""
        self.NameLabel.setText(f"名称: {Plugin.Name}")
        self.PathLabel.setText(f"路径: {Plugin.Path}")
        self.VersionLabel.setText(f"版本: {Plugin.Version or '-'}")
        self.AuthorLabel.setText(f"作者: {Plugin.CreatedBy or '-'}")
        self.CategoryLabel.setText(f"分类: {Plugin.Category or '-'}")
        self.DescriptionEdit.setText(Plugin.Description or "无描述")

        # 依赖
        Dependencies = self.Manager.GetDependencies(Plugin.Name)
        self.DependenciesEdit.setText(", ".join(Dependencies) if Dependencies else "无")

        # 被依赖
        Dependents = self.Manager.GetDependents(Plugin.Name)
        self.DependentsEdit.setText(", ".join(Dependents) if Dependents else "无")

        # 启用状态
        self.EnabledCheck.blockSignals(True)
        if Plugin.EnabledInProject is True:
            self.EnabledCheck.setChecked(True)
        elif Plugin.EnabledInProject is False:
            self.EnabledCheck.setChecked(False)
        else:
            self.EnabledCheck.setChecked(Plugin.EnabledByDefault)
        self.EnabledCheck.blockSignals(False)

        # 保存当前插件名
        self._CurPluginName = Plugin.Name
        self._CurPluginPath = Plugin.Path

    def _OnEnabledChanged(self, State: int):
        """启用状态变更"""
        if not hasattr(self, "_CurPluginName"):
            return

        Enabled = State == Qt.Checked
        if self.Manager.SetPluginEnabled(self._CurPluginName, Enabled):
            self._RefreshPluginList()
            # 更新状态栏
            Stats = self.Manager.GetStats()
            self.StatusBar.showMessage(
                f"共 {Stats['Total']} 个插件 | "
                f"项目: {Stats['Project']} | 引擎: {Stats['Engine']} | "
                f"已启用: {Stats['Enabled']} | 已禁用: {Stats['Disabled']}"
            )
        else:
            QMessageBox.warning(self, "错误", "修改失败")

    def _OnOpenFolder(self):
        """打开插件目录"""
        if not hasattr(self, "_CurPluginPath"):
            return
        import subprocess
        subprocess.Popen(f'explorer "{self._CurPluginPath}"')

    def _OnOpenProjectFolder(self):
        """打开项目目录"""
        if not self.Manager.ProjectInfo:
            return
        import subprocess
        subprocess.Popen(f'explorer "{self.Manager.ProjectInfo.Path}"')

    def _OnOpenEngineFolder(self):
        """打开引擎目录"""
        if not self.Manager.ProjectInfo or not self.Manager.ProjectInfo.EnginePath:
            QMessageBox.warning(self, "提示", "未找到引擎目录")
            return
        import subprocess
        subprocess.Popen(f'explorer "{self.Manager.ProjectInfo.EnginePath}"')
