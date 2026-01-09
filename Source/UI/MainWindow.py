# 主窗口
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QLabel, QTextEdit,
    QGroupBox, QCheckBox, QPushButton, QMessageBox, QHeaderView, QStatusBar, QTabBar, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from Source.Logic.PluginManager import PluginManager
from Source.Data.PluginReader import PluginInfo, PluginSource
from Source.Data.ConfigCache import ConfigCache


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.Manager = PluginManager()
        self.Config = ConfigCache()
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

        # 左右分栏
        Splitter = QSplitter(Qt.Horizontal)

        # 左侧：信息区 + 插件列表
        LeftWidget = QWidget()
        LeftLayout = QVBoxLayout(LeftWidget)
        LeftLayout.setContentsMargins(0, 0, 0, 0)
        self._CreateInfoPanel(LeftLayout)
        LeftLayout.addWidget(self._CreatePluginList())
        Splitter.addWidget(LeftWidget)

        # 右侧：重新加载 + 插件详情
        RightWidget = QWidget()
        RightLayout = QVBoxLayout(RightWidget)
        RightLayout.setContentsMargins(0, 0, 0, 0)
        self._CreateButtonRow(RightLayout)
        RightLayout.addWidget(self._CreateDetailPanel())
        Splitter.addWidget(RightWidget)

        Splitter.setSizes([600, 400])
        MainLayout.addWidget(Splitter)

        # 状态栏
        self.StatusBar = QStatusBar()
        self.StatusLabel = QLabel()
        self.StatusBar.addPermanentWidget(self.StatusLabel)
        self.setStatusBar(self.StatusBar)

    def _CreateInfoPanel(self, ParentLayout: QVBoxLayout):
        """创建项目信息区"""
        # 项目信息
        ProjectRow = QHBoxLayout()
        LblProjectName = QLabel("项目名称:")
        LblProjectName.setFixedWidth(60)
        ProjectRow.addWidget(LblProjectName)
        self.ProjectNameLabel = QLabel()
        self.ProjectNameLabel.setFixedWidth(120)
        ProjectRow.addWidget(self.ProjectNameLabel)
        LblProjectDir = QLabel("目录:")
        LblProjectDir.setFixedWidth(30)
        ProjectRow.addWidget(LblProjectDir)
        self.ProjectPathLabel = QLabel()
        self.ProjectPathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ProjectRow.addWidget(self.ProjectPathLabel, 1)
        self.OpenProjectBtn = QPushButton("打开目录")
        self.OpenProjectBtn.clicked.connect(self._OnOpenProjectFolder)
        ProjectRow.addWidget(self.OpenProjectBtn)
        ParentLayout.addLayout(ProjectRow)

        # 引擎信息
        EngineRow = QHBoxLayout()
        LblEngineName = QLabel("引擎名称:")
        LblEngineName.setFixedWidth(60)
        EngineRow.addWidget(LblEngineName)
        self.EngineVersionLabel = QLabel()
        self.EngineVersionLabel.setFixedWidth(120)
        EngineRow.addWidget(self.EngineVersionLabel)
        LblEngineDir = QLabel("目录:")
        LblEngineDir.setFixedWidth(30)
        EngineRow.addWidget(LblEngineDir)
        self.EnginePathLabel = QLabel()
        self.EnginePathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        EngineRow.addWidget(self.EnginePathLabel, 1)
        self.OpenEngineBtn = QPushButton("打开目录")
        self.OpenEngineBtn.clicked.connect(self._OnOpenEngineFolder)
        EngineRow.addWidget(self.OpenEngineBtn)
        ParentLayout.addLayout(EngineRow)

    def _CreateButtonRow(self, ParentLayout: QVBoxLayout):
        """创建按钮行"""
        Container = QWidget()
        Container.setFixedHeight(52)
        Layout = QVBoxLayout(Container)
        Layout.setContentsMargins(0, 0, 0, 0)
        Row = QHBoxLayout()
        Row.addStretch()
        self.ReloadBtn = QPushButton("重新加载")
        self.ReloadBtn.clicked.connect(self._OnReload)
        Row.addWidget(self.ReloadBtn)
        Layout.addLayout(Row)
        Layout.addStretch()
        ParentLayout.addWidget(Container)

    def _CreatePluginList(self) -> QWidget:
        """创建插件列表"""
        GroupBox = QGroupBox("插件列表")
        Layout = QVBoxLayout(GroupBox)

        # 搜索栏
        SearchLayout = QHBoxLayout()
        self.SearchFieldCombo = QComboBox()
        self.SearchFieldCombo.addItems(["名称", "作者", "分类", "描述", "依赖", "被依赖"])
        self.SearchFieldCombo.setCurrentIndex(self.Config.Get("SearchField", 0))
        self.SearchFieldCombo.currentIndexChanged.connect(self._OnSearchFieldChanged)
        self.SearchFieldCombo.setFixedWidth(80)
        SearchLayout.addWidget(self.SearchFieldCombo)

        self.SearchEdit = QLineEdit()
        self.SearchEdit.setPlaceholderText("搜索插件...")
        self.SearchEdit.setClearButtonEnabled(True)
        self.SearchEdit.textChanged.connect(self._OnSearch)
        SearchLayout.addWidget(self.SearchEdit)
        Layout.addLayout(SearchLayout)

        # 标签页
        self.SourceTabs = QTabBar()
        self.SourceTabs.addTab("项目")
        self.SourceTabs.addTab("Fab")
        self.SourceTabs.addTab("引擎")
        self.SourceTabs.currentChanged.connect(self._OnTabChanged)
        Layout.addWidget(self.SourceTabs)

        self.PluginTree = QTreeWidget()
        self.PluginTree.setHeaderLabels(["名称", "分类", "状态"])
        self.PluginTree.setRootIsDecorated(False)
        self.PluginTree.setAlternatingRowColors(True)
        self.PluginTree.setSortingEnabled(True)
        self.PluginTree.sortByColumn(0, Qt.AscendingOrder)
        self.PluginTree.itemSelectionChanged.connect(self._OnPluginSelected)

        Header = self.PluginTree.header()
        Header.setSectionResizeMode(0, QHeaderView.Stretch)
        Header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        Header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        Layout.addWidget(self.PluginTree)

        return GroupBox

    def _CreateDetailPanel(self) -> QWidget:
        """创建详情面板"""
        self.DetailPanel = QGroupBox("插件详情")
        self.DetailPanel.setEnabled(False)
        Layout = QVBoxLayout(self.DetailPanel)

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

        return self.DetailPanel

    def _LoadProject(self, ProjectPath: Path):
        """加载项目"""
        if not self.Manager.LoadProject(ProjectPath):
            return

        Info = self.Manager.ProjectInfo
        self.ProjectNameLabel.setText(Info.Name if Info else "-")
        self.ProjectPathLabel.setText(str(ProjectPath))

        # 显示引擎信息
        if Info and Info.EnginePath:
            self.EngineVersionLabel.setText(Info.EngineVersion)
            self.EnginePathLabel.setText(str(Info.EnginePath))
        elif Info:
            self.EngineVersionLabel.setText(Info.EngineVersion)
            self.EnginePathLabel.setText("未找到")
        else:
            self.EngineVersionLabel.setText("-")
            self.EnginePathLabel.setText("-")

        # 刷新列表
        self._RefreshPluginList()

        # 更新状态栏
        Stats = self.Manager.GetStats()
        self.StatusLabel.setText(
            f"共 {Stats['Total']} 个插件 | "
            f"项目: {Stats['Project']} | 引擎: {Stats['Engine']} | Fab: {Stats['Fab']} | "
            f"已启用: {Stats['Enabled']} | 已禁用: {Stats['Disabled']}"
        )

    def _GetSourceByTabIndex(self, Index: int) -> PluginSource:
        """根据标签页索引获取来源类型"""
        if Index == 0:
            return PluginSource.Project
        elif Index == 1:
            return PluginSource.Fab
        else:
            return PluginSource.Engine

    def _RefreshPluginList(self):
        """刷新插件列表"""
        self.PluginTree.clear()

        # 获取当前标签页对应的来源类型
        CurSource = self._GetSourceByTabIndex(self.SourceTabs.currentIndex())

        # 更新各标签页的匹配数
        AllPlugins = self.Manager.GetPlugins()
        ProjectCount = len([P for P in AllPlugins if P.Source == PluginSource.Project])
        EngineCount = len([P for P in AllPlugins if P.Source == PluginSource.Engine])
        FabCount = len([P for P in AllPlugins if P.Source == PluginSource.Fab])

        self.SourceTabs.setTabText(0, f"项目 ({ProjectCount})")
        self.SourceTabs.setTabText(1, f"Fab ({FabCount})")
        self.SourceTabs.setTabText(2, f"引擎 ({EngineCount})")

        # 只显示当前标签页类型的插件
        Plugins = [P for P in AllPlugins if P.Source == CurSource]
        for Plugin in Plugins:
            Item = QTreeWidgetItem()
            Item.setText(0, Plugin.Name)
            Item.setText(1, Plugin.Category or "-")

            # 状态
            if Plugin.EnabledInProject is True:
                Status = "启用"
            elif Plugin.EnabledInProject is False:
                Status = "禁用"
            else:
                Status = "默认" + ("(启用)" if Plugin.EnabledByDefault else "(禁用)")
            Item.setText(2, Status)

            Item.setData(0, Qt.UserRole, Plugin.Name)
            self.PluginTree.addTopLevelItem(Item)

    def _OnSearch(self, Text: str):
        """搜索"""
        Field = self.SearchFieldCombo.currentIndex()
        self.Manager.Search(Text, Field)
        self._RefreshPluginList()

    def _OnSearchFieldChanged(self, Index: int):
        """搜索字段变更"""
        self.Config.Set("SearchField", Index)
        self._OnSearch(self.SearchEdit.text())

    def _OnTabChanged(self, Index: int):
        """标签页切换"""
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
        self.DetailPanel.setEnabled(True)
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
            self.StatusLabel.setText(
                f"共 {Stats['Total']} 个插件 | "
                f"项目: {Stats['Project']} | 引擎: {Stats['Engine']} | Fab: {Stats['Fab']} | "
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

    def _OnReload(self):
        """重新加载插件"""
        if not self.Manager.ProjectInfo:
            return
        self._LoadProject(self.Manager.ProjectInfo.Path)
