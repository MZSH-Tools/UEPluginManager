# 主窗口
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QLabel, QTextEdit,
    QGroupBox, QCheckBox, QPushButton, QMessageBox, QHeaderView, QStatusBar, QTabBar, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush

from Source.Logic.PluginManager import PluginManager
from Source.Data.PluginReader import PluginInfo, PluginSource


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.Manager = PluginManager()
        self.CurSource: PluginSource = PluginSource.Project
        self.InitUI()
        self.LoadProject(Path.cwd())

    def InitUI(self):
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
        self.CreateInfoPanel(LeftLayout)
        LeftLayout.addWidget(self.CreatePluginList())
        Splitter.addWidget(LeftWidget)

        # 右侧：重新加载 + 插件详情
        RightWidget = QWidget()
        RightLayout = QVBoxLayout(RightWidget)
        RightLayout.setContentsMargins(0, 0, 0, 0)
        self.CreateButtonRow(RightLayout)
        RightLayout.addWidget(self.CreateDetailPanel())
        Splitter.addWidget(RightWidget)

        Splitter.setSizes([600, 400])
        MainLayout.addWidget(Splitter)

        # 状态栏
        self.StatusBar = QStatusBar()
        self.StatusLeftLabel = QLabel()
        self.StatusRightLabel = QLabel()
        self.StatusBar.addWidget(self.StatusLeftLabel)
        self.StatusBar.addPermanentWidget(self.StatusRightLabel)
        self.setStatusBar(self.StatusBar)

    def CreateInfoPanel(self, ParentLayout: QVBoxLayout):
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
        self.OpenProjectBtn.clicked.connect(self.OnOpenProjectFolder)
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
        self.OpenEngineBtn.clicked.connect(self.OnOpenEngineFolder)
        EngineRow.addWidget(self.OpenEngineBtn)
        ParentLayout.addLayout(EngineRow)

    def CreateButtonRow(self, ParentLayout: QVBoxLayout):
        """创建按钮行"""
        Container = QWidget()
        Layout = QVBoxLayout(Container)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(8)

        # 关闭项目
        CloseRow = QHBoxLayout()
        self.CloseProjectBtn = QPushButton("关闭项目")
        self.CloseProjectBtn.setFixedWidth(80)
        self.CloseProjectBtn.clicked.connect(self.OnCloseProject)
        CloseRow.addWidget(self.CloseProjectBtn)
        CloseTip = QLabel("建议在项目关闭时进行修改，以避免未知错误")
        CloseTip.setStyleSheet("color: gray;")
        CloseRow.addWidget(CloseTip)
        CloseRow.addStretch()
        Layout.addLayout(CloseRow)

        # 重新加载
        ReloadRow = QHBoxLayout()
        self.ReloadBtn = QPushButton("重新加载")
        self.ReloadBtn.setFixedWidth(80)
        self.ReloadBtn.clicked.connect(self.OnReload)
        ReloadRow.addWidget(self.ReloadBtn)
        ReloadTip = QLabel("在外部修改插件后点击刷新界面")
        ReloadTip.setStyleSheet("color: gray;")
        ReloadRow.addWidget(ReloadTip)
        ReloadRow.addStretch()
        Layout.addLayout(ReloadRow)

        ParentLayout.addWidget(Container)

    def CreatePluginList(self) -> QWidget:
        """创建插件列表"""
        GroupBox = QGroupBox("插件列表")
        Layout = QVBoxLayout(GroupBox)

        # 搜索栏
        SearchLayout = QHBoxLayout()
        self.SearchFieldCombo = QComboBox()
        self.SearchFieldCombo.addItems(["名称", "作者", "分类", "描述", "依赖", "被依赖"])
        self.SearchFieldCombo.currentIndexChanged.connect(self.OnSearchFieldChanged)
        self.SearchFieldCombo.setFixedWidth(80)
        SearchLayout.addWidget(self.SearchFieldCombo)

        self.SearchEdit = QLineEdit()
        self.SearchEdit.setPlaceholderText("搜索插件...")
        self.SearchEdit.setClearButtonEnabled(True)
        self.SearchEdit.textChanged.connect(self.OnSearch)
        SearchLayout.addWidget(self.SearchEdit)
        Layout.addLayout(SearchLayout)

        # 标签页
        self.SourceTabs = QTabBar()
        self.SourceTabs.addTab("项目")
        self.SourceTabs.addTab("商城")
        self.SourceTabs.addTab("引擎")
        self.SourceTabs.currentChanged.connect(self.OnTabChanged)
        Layout.addWidget(self.SourceTabs)

        self.PluginTree = QTreeWidget()
        self.PluginTree.setHeaderLabels(["名称", "作者", "分类", "状态"])
        self.PluginTree.setRootIsDecorated(False)
        self.PluginTree.setSortingEnabled(True)
        self.PluginTree.sortByColumn(0, Qt.AscendingOrder)
        self.PluginTree.itemSelectionChanged.connect(self.OnPluginSelected)

        Header = self.PluginTree.header()
        Header.setSectionsMovable(False)
        Header.setStretchLastSection(False)
        Header.setSectionResizeMode(0, QHeaderView.Stretch)
        Header.setSectionResizeMode(1, QHeaderView.Fixed)
        Header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        Header.setSectionResizeMode(3, QHeaderView.Fixed)
        Header.resizeSection(1, 120)
        Header.resizeSection(3, 80)

        Layout.addWidget(self.PluginTree)

        return GroupBox

    def CreateDetailPanel(self) -> QWidget:
        """创建详情面板"""
        self.DetailPanel = QGroupBox("插件详情")
        self.DetailPanel.setEnabled(False)
        Layout = QVBoxLayout(self.DetailPanel)

        # 基本信息
        InfoLayout = QVBoxLayout()

        self.NameLabel = QLabel("名称: -")
        self.NameLabel.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        InfoLayout.addWidget(self.NameLabel)

        self.FolderLabel = QLabel("目录: -")
        InfoLayout.addWidget(self.FolderLabel)

        self.DocsLabel = QLabel("文档: -")
        self.DocsLabel.setOpenExternalLinks(True)
        self.DocsLabel.setWordWrap(True)
        InfoLayout.addWidget(self.DocsLabel)

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

        # 按钮区
        BtnLayout = QVBoxLayout()
        BtnLayout.setSpacing(8)

        # 启用复选框
        EnableRow = QHBoxLayout()
        self.EnabledCheck = QCheckBox("启用插件")
        self.EnabledCheck.setFixedWidth(80)
        self.EnabledCheck.clicked.connect(self.OnEnabledClicked)
        EnableRow.addWidget(self.EnabledCheck)
        EnableTip = QLabel("在项目中启用或禁用此插件")
        EnableTip.setStyleSheet("color: gray;")
        EnableRow.addWidget(EnableTip)
        EnableRow.addStretch()
        BtnLayout.addLayout(EnableRow)

        # 恢复默认
        ResetRow = QHBoxLayout()
        self.ResetDefaultBtn = QPushButton("恢复默认")
        self.ResetDefaultBtn.setFixedWidth(80)
        self.ResetDefaultBtn.clicked.connect(self.OnResetDefault)
        ResetRow.addWidget(self.ResetDefaultBtn)
        ResetTip = QLabel("移除项目配置，使用插件默认状态")
        ResetTip.setStyleSheet("color: gray;")
        ResetRow.addWidget(ResetTip)
        ResetRow.addStretch()
        BtnLayout.addLayout(ResetRow)

        # 打开目录
        OpenRow = QHBoxLayout()
        self.OpenFolderBtn = QPushButton("打开目录")
        self.OpenFolderBtn.setFixedWidth(80)
        self.OpenFolderBtn.clicked.connect(self.OnOpenFolder)
        OpenRow.addWidget(self.OpenFolderBtn)
        OpenTip = QLabel("在资源管理器中打开插件目录")
        OpenTip.setStyleSheet("color: gray;")
        OpenRow.addWidget(OpenTip)
        OpenRow.addStretch()
        BtnLayout.addLayout(OpenRow)

        # 目录修正
        FixRow = QHBoxLayout()
        self.FixFolderBtn = QPushButton("目录修正")
        self.FixFolderBtn.setFixedWidth(80)
        self.FixFolderBtn.clicked.connect(self.OnFixFolder)
        FixRow.addWidget(self.FixFolderBtn)
        FixTip = QLabel("将目录重命名为插件同名")
        FixTip.setStyleSheet("color: gray;")
        FixRow.addWidget(FixTip)
        FixRow.addStretch()
        BtnLayout.addLayout(FixRow)

        # 删除插件
        DeleteRow = QHBoxLayout()
        self.DeletePluginBtn = QPushButton("删除插件")
        self.DeletePluginBtn.setFixedWidth(80)
        self.DeletePluginBtn.clicked.connect(self.OnDeletePlugin)
        DeleteRow.addWidget(self.DeletePluginBtn)
        DeleteTip = QLabel("将插件移至回收站")
        DeleteTip.setStyleSheet("color: gray;")
        DeleteRow.addWidget(DeleteTip)
        DeleteRow.addStretch()
        BtnLayout.addLayout(DeleteRow)

        Layout.addLayout(BtnLayout)
        Layout.addStretch()

        return self.DetailPanel

    def LoadProject(self, ProjectPath: Path, AutoSelect: bool = True):
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
        self.RefreshPluginList()
        if AutoSelect:
            self.SelectFirstOrClear()

        # 更新状态栏
        self.UpdateStatusBar()

    def GetSourceByTabIndex(self, Index: int) -> PluginSource:
        """根据标签页索引获取来源类型"""
        if Index == 0:
            return PluginSource.Project
        elif Index == 1:
            return PluginSource.Fab
        else:
            return PluginSource.Engine

    def RefreshPluginList(self):
        """刷新插件列表（不改变选中状态）"""
        # 阻止信号，防止 clear() 触发不必要的事件
        self.PluginTree.blockSignals(True)
        self.PluginTree.clear()
        self.PluginTree.blockSignals(False)

        # 获取当前标签页对应的来源类型
        self.CurSource = self.GetSourceByTabIndex(self.SourceTabs.currentIndex())

        # 更新各标签页的匹配数
        ProjectCount = len(self.Manager.GetPlugins(PluginSource.Project))
        FabCount = len(self.Manager.GetPlugins(PluginSource.Fab))
        EngineCount = len(self.Manager.GetPlugins(PluginSource.Engine))

        self.SourceTabs.setTabText(0, f"项目 ({ProjectCount})")
        self.SourceTabs.setTabText(1, f"商城 ({FabCount})")
        self.SourceTabs.setTabText(2, f"引擎 ({EngineCount})")

        # 只显示当前标签页类型的插件
        RedBrush = QBrush(QColor(220, 50, 50))
        Plugins = self.Manager.GetPlugins(self.CurSource)
        for Plugin in Plugins:
            Item = QTreeWidgetItem()
            Item.setText(0, Plugin.Name)
            Item.setText(1, Plugin.CreatedBy or "-")
            Item.setText(2, Plugin.Category or "-")

            # 检查是否冲突
            HasConflict = self.Manager.HasConflict(Plugin.Name)

            # 状态
            if HasConflict:
                Status = "冲突"
                Item.setForeground(3, RedBrush)
            elif Plugin.EnabledInProject is True:
                Status = "启用"
            elif Plugin.EnabledInProject is False:
                Status = "禁用"
            else:
                Status = "默认" + ("(启用)" if Plugin.EnabledByDefault else "(禁用)")
            Item.setText(3, Status)

            Item.setData(0, Qt.UserRole, Plugin.Name)
            self.PluginTree.addTopLevelItem(Item)

    def SelectFirstOrClear(self):
        """选中第一个插件，如果列表为空则置灰详情面板"""
        if self.PluginTree.topLevelItemCount() > 0:
            self.PluginTree.setCurrentItem(self.PluginTree.topLevelItem(0))
        else:
            self.ClearDetailPanel()

    def TryReselectOrFirst(self):
        """尝试重新选中当前插件，失败则选第一个或置灰"""
        if self.PluginTree.topLevelItemCount() == 0:
            self.ClearDetailPanel()
            return

        # 尝试重新选中之前的插件
        if hasattr(self, "CurPluginName"):
            for i in range(self.PluginTree.topLevelItemCount()):
                Item = self.PluginTree.topLevelItem(i)
                if Item.data(0, Qt.UserRole) == self.CurPluginName:
                    self.PluginTree.setCurrentItem(Item)
                    return

        # 找不到就选第一个
        self.PluginTree.setCurrentItem(self.PluginTree.topLevelItem(0))

    def OnSearch(self, Text: str):
        """搜索"""
        Field = self.SearchFieldCombo.currentIndex()
        self.Manager.Search(Text, Field)
        self.RefreshPluginList()
        self.SelectFirstOrClear()

    def OnSearchFieldChanged(self, Index: int):
        """搜索字段变更"""
        self.OnSearch(self.SearchEdit.text())

    def OnTabChanged(self, Index: int):
        """标签页切换"""
        self.RefreshPluginList()
        self.SelectFirstOrClear()

    def OnPluginSelected(self):
        """插件选中"""
        Items = self.PluginTree.selectedItems()
        if not Items:
            return

        PluginName = Items[0].data(0, Qt.UserRole)
        Plugin = self.Manager.GetPluginByName(PluginName, self.CurSource)
        if not Plugin:
            return

        self.ShowPluginDetail(Plugin)

    def ShowPluginDetail(self, Plugin: PluginInfo):
        """显示插件详情"""
        self.DetailPanel.setEnabled(True)
        self.NameLabel.setText(f"名称: {Plugin.Name}")
        self.FolderLabel.setText(f"目录: {Plugin.Path.name}")
        if Plugin.DocsURL:
            self.DocsLabel.setText(f'文档: <a href="{Plugin.DocsURL}">{Plugin.DocsURL}</a>')
        else:
            self.DocsLabel.setText("文档: -")
        self.AuthorLabel.setText(f"作者: {Plugin.CreatedBy or '-'}")
        self.CategoryLabel.setText(f"分类: {Plugin.Category or '-'}")
        self.DescriptionEdit.setText(Plugin.Description or "无描述")

        # 依赖
        Dependencies = self.Manager.GetDependencies(Plugin.Name, self.CurSource)
        self.DependenciesEdit.setText(", ".join(Dependencies) if Dependencies else "无")

        # 被依赖
        Dependents = self.Manager.GetDependents(Plugin.Name, self.CurSource)
        self.DependentsEdit.setText(", ".join(Dependents) if Dependents else "无")

        # 检查冲突
        self.CurHasConflict = self.Manager.HasConflict(Plugin.Name)

        # 启用状态（clicked 信号只响应用户点击，程序修改不会触发）
        if self.CurHasConflict:
            # 冲突时不勾选
            self.EnabledCheck.setChecked(False)
        elif Plugin.EnabledInProject is True:
            self.EnabledCheck.setChecked(True)
        elif Plugin.EnabledInProject is False:
            self.EnabledCheck.setChecked(False)
        else:
            self.EnabledCheck.setChecked(Plugin.EnabledByDefault)

        # 保存当前插件名
        self.CurPluginName = Plugin.Name
        self.CurPluginPath = Plugin.Path

        # 引擎插件不可删除
        self.DeletePluginBtn.setEnabled(self.CurSource != PluginSource.Engine)

        # 路径修正（文件夹名与插件名不一致且非引擎插件时可用）
        CanFix = Plugin.Path.name != Plugin.Name and self.CurSource != PluginSource.Engine
        self.FixFolderBtn.setEnabled(CanFix)

    def ClearDetailPanel(self):
        """清空并置灰详情面板"""
        self.DetailPanel.setEnabled(False)
        self.NameLabel.setText("名称: -")
        self.FolderLabel.setText("目录: -")
        self.DocsLabel.setText("文档: -")
        self.AuthorLabel.setText("作者: -")
        self.CategoryLabel.setText("分类: -")
        self.DescriptionEdit.setText("")
        self.DependenciesEdit.setText("")
        self.DependentsEdit.setText("")
        self.EnabledCheck.setChecked(False)
        if hasattr(self, "CurPluginName"):
            del self.CurPluginName
        if hasattr(self, "CurPluginPath"):
            del self.CurPluginPath
        self.CurHasConflict = False

    def OnEnabledClicked(self, Checked: bool):
        """用户点击启用复选框"""
        if not hasattr(self, "CurPluginName"):
            return

        # 冲突时弹出二选一对话框
        if getattr(self, "CurHasConflict", False) and Checked:
            self.HandleConflictEnable()
            return

        if Checked:
            self.EnablePluginWithDeps(self.CurPluginName, self.CurSource)
        else:
            self.DisablePluginWithDeps(self.CurPluginName, self.CurSource)

    def HandleConflictEnable(self):
        """处理冲突插件启用（提示用户）"""
        PluginName = self.CurPluginName
        CurPlugin = self.Manager.GetPluginByName(PluginName, self.CurSource)
        Conflict = self.Manager.GetConflictingPlugin(PluginName, self.CurSource)

        if not CurPlugin or not Conflict:
            self.EnabledCheck.setChecked(False)
            return

        ConflictPlugin, ConflictSource = Conflict

        SourceNames = {
            PluginSource.Project: "项目",
            PluginSource.Engine: "引擎",
            PluginSource.Fab: "商城"
        }

        CurSourceName = SourceNames[self.CurSource]
        ConflictSourceName = SourceNames[ConflictSource]

        QMessageBox.warning(
            self, "同名插件冲突",
            f"插件 {PluginName} 在 {CurSourceName} 和 {ConflictSourceName} 中都存在。\n\n"
            f"UE 不支持同名插件，请手动删除其中一个后再启用。"
        )

        self.EnabledCheck.setChecked(False)

    def EnablePluginWithDeps(self, PluginName: str, Source):
        """启用插件及其依赖"""
        DisabledDeps = self.Manager.GetDisabledDependencies(PluginName, Source)
        PluginsToEnable = [(PluginName, Source)]

        if DisabledDeps:
            DepNames = [f"  - {Name}" for Name, _ in DisabledDeps]
            Msg = f"插件 {PluginName} 依赖以下未启用的插件：\n" + "\n".join(DepNames) + "\n\n是否一并启用？"
            Reply = QMessageBox.question(self, "依赖确认", Msg, QMessageBox.Yes | QMessageBox.Cancel)
            if Reply != QMessageBox.Yes:
                # 确保状态恢复（对话框可能导致状态丢失）
                self.CurPluginName = PluginName
                self.CurSource = Source
                self.RestoreCheckbox(PluginName, Source)
                return
            PluginsToEnable = DisabledDeps + PluginsToEnable

        self.ApplyPluginChanges(PluginsToEnable, True)

    def DisablePluginWithDeps(self, PluginName: str, Source):
        """禁用插件及依赖它的插件"""
        EnabledDependents = self.Manager.GetDisabledDependents(PluginName)
        PluginsToDisable = [(PluginName, Source)]

        if EnabledDependents:
            DepNames = [f"  - {Name}" for Name, _ in EnabledDependents]
            Msg = f"以下插件依赖 {PluginName}：\n" + "\n".join(DepNames) + "\n\n禁用后这些插件也将被禁用，是否继续？"
            Reply = QMessageBox.question(self, "依赖确认", Msg, QMessageBox.Yes | QMessageBox.Cancel)
            if Reply != QMessageBox.Yes:
                # 确保状态恢复（对话框可能导致状态丢失）
                self.CurPluginName = PluginName
                self.CurSource = Source
                self.RestoreCheckbox(PluginName, Source)
                return
            PluginsToDisable = EnabledDependents + PluginsToDisable

        self.ApplyPluginChanges(PluginsToDisable, False)

    def RestoreCheckbox(self, PluginName: str, Source):
        """恢复复选框状态"""
        Plugin = self.Manager.GetPluginByName(PluginName, Source)
        if Plugin:
            if Plugin.EnabledInProject is True:
                self.EnabledCheck.setChecked(True)
            elif Plugin.EnabledInProject is False:
                self.EnabledCheck.setChecked(False)
            else:
                self.EnabledCheck.setChecked(Plugin.EnabledByDefault)

    def ApplyPluginChanges(self, Plugins: list, Enabled: bool):
        """批量应用插件状态变更"""
        Success = True
        for Name, Source in Plugins:
            if not self.Manager.SetPluginEnabled(Name, Source, Enabled):
                Success = False

        if Success:
            self.RefreshPluginList()
            self.TryReselectOrFirst()
            self.UpdateStatusBar()
        else:
            QMessageBox.warning(self, "错误", "部分插件修改失败")

    def OnResetDefault(self):
        """恢复插件默认状态"""
        if not hasattr(self, "CurPluginName"):
            return

        Plugin = self.Manager.GetPluginByName(self.CurPluginName, self.CurSource)
        if not Plugin:
            return

        # 已经是默认状态
        if Plugin.EnabledInProject is None:
            return

        if self.Manager.ResetPluginToDefault(self.CurPluginName, self.CurSource):
            self.RefreshPluginList()
            self.TryReselectOrFirst()
            self.UpdateStatusBar()

    def OnDeletePlugin(self):
        """删除插件"""
        if not hasattr(self, "CurPluginName"):
            return

        # 引擎插件不可删除
        if self.CurSource == PluginSource.Engine:
            return

        Plugin = self.Manager.GetPluginByName(self.CurPluginName, self.CurSource)
        if not Plugin:
            return

        SourceNames = {PluginSource.Project: "项目", PluginSource.Fab: "商城"}
        SourceName = SourceNames.get(self.CurSource, "")

        Reply = QMessageBox.warning(
            self, "确认删除",
            f"确定要删除{SourceName}插件 {self.CurPluginName} 吗？\n\n路径: {Plugin.Path}\n\n此操作会将插件移至回收站。",
            QMessageBox.Yes | QMessageBox.Cancel
        )

        if Reply != QMessageBox.Yes:
            return

        if self.Manager.DeletePlugin(self.CurPluginName, self.CurSource):
            self.RefreshPluginList()
            self.SelectFirstOrClear()
            self.UpdateStatusBar()
        else:
            QMessageBox.warning(self, "错误", "删除插件失败")

    def OnFixFolder(self):
        """修正文件夹名称"""
        if not hasattr(self, "CurPluginName"):
            return

        Plugin = self.Manager.GetPluginByName(self.CurPluginName, self.CurSource)
        if not Plugin:
            return

        OldName = Plugin.Path.name
        NewName = Plugin.Name

        Reply = QMessageBox.question(
            self, "确认修正",
            f"将目录重命名为插件同名：\n\n{OldName}\n→ {NewName}\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.Cancel
        )

        if Reply != QMessageBox.Yes:
            return

        if self.Manager.RenamePluginFolder(self.CurPluginName, self.CurSource):
            # 更新目录显示
            self.FolderLabel.setText(f"目录: {Plugin.Path.name}")
            self.CurPluginPath = Plugin.Path
            self.FixFolderBtn.setEnabled(False)
            QMessageBox.information(self, "成功", "目录已修正")
        else:
            QMessageBox.warning(self, "错误", "修正目录失败")

    def OnOpenFolder(self):
        """打开插件目录"""
        if not hasattr(self, "CurPluginPath"):
            return
        import subprocess
        subprocess.Popen(f'explorer "{self.CurPluginPath}"')

    def OnOpenProjectFolder(self):
        """打开项目目录"""
        if not self.Manager.ProjectInfo:
            return
        import subprocess
        subprocess.Popen(f'explorer "{self.Manager.ProjectInfo.Path}"')

    def OnOpenEngineFolder(self):
        """打开引擎目录"""
        if not self.Manager.ProjectInfo or not self.Manager.ProjectInfo.EnginePath:
            QMessageBox.warning(self, "提示", "未找到引擎目录")
            return
        import subprocess
        subprocess.Popen(f'explorer "{self.Manager.ProjectInfo.EnginePath}"')

    def UpdateStatusBar(self):
        """更新状态栏"""
        Stats = self.Manager.GetStats()
        self.StatusLeftLabel.setText(
            f"共 {Stats['Total']} 个插件 | "
            f"项目: {Stats['Project']} | 商城: {Stats['Fab']} | 引擎: {Stats['Engine']}"
        )
        self.StatusRightLabel.setText(
            f"已启用: {Stats['Enabled']} | 已禁用: {Stats['Disabled']}"
        )

    def OnReload(self):
        """重新加载插件"""
        if not self.Manager.ProjectInfo:
            return
        PrevPluginName = getattr(self, "CurPluginName", None)
        self.LoadProject(self.Manager.ProjectInfo.Path, AutoSelect=False)
        if PrevPluginName:
            self.CurPluginName = PrevPluginName
        self.TryReselectOrFirst()

    def OnCloseProject(self):
        """关闭项目（尝试关闭 UE 编辑器）"""
        if not self.Manager.ProjectInfo:
            return

        import subprocess
        ProjectName = self.Manager.ProjectInfo.Name

        Reply = QMessageBox.question(
            self, "关闭项目",
            f"将尝试关闭 UE 编辑器中的项目 {ProjectName}。\n\n"
            f"请确保已保存所有更改，是否继续？",
            QMessageBox.Yes | QMessageBox.Cancel
        )

        if Reply != QMessageBox.Yes:
            return

        # 尝试关闭包含项目名的 UE 编辑器进程
        try:
            subprocess.run(
                f'taskkill /FI "WINDOWTITLE eq {ProjectName}*" /IM UnrealEditor.exe',
                shell=True, capture_output=True
            )
        except Exception:
            pass
