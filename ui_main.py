# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainDQVggF.ui'
##
## Created by: Qt User Interface Compiler version 5.15.5
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 720)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionLoad = QAction(MainWindow)
        self.actionLoad.setObjectName(u"actionLoad")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_3 = QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, 0, -1, 0)
        self.frameNumber = QLabel(self.centralwidget)
        self.frameNumber.setObjectName(u"frameNumber")
        self.frameNumber.setMinimumSize(QSize(0, 30))
        self.frameNumber.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.frameNumber)

        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(10)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.gridLayout.setContentsMargins(-1, 10, -1, 10)
        self.seekButton = QPushButton(self.centralwidget)
        self.seekButton.setObjectName(u"seekButton")
        self.seekButton.setEnabled(False)
        self.seekButton.setMinimumSize(QSize(80, 0))
        self.seekButton.setMaximumSize(QSize(80, 16777215))

        self.gridLayout.addWidget(self.seekButton, 3, 2, 1, 1)

        self.nextFrameButton = QPushButton(self.centralwidget)
        self.nextFrameButton.setObjectName(u"nextFrameButton")
        self.nextFrameButton.setEnabled(False)
        self.nextFrameButton.setMinimumSize(QSize(80, 0))
        self.nextFrameButton.setMaximumSize(QSize(80, 16777215))

        self.gridLayout.addWidget(self.nextFrameButton, 2, 2, 1, 1)

        self.resetViewButton = QPushButton(self.centralwidget)
        self.resetViewButton.setObjectName(u"resetViewButton")
        self.resetViewButton.setEnabled(False)

        self.gridLayout.addWidget(self.resetViewButton, 4, 0, 1, 3)

        self.prevFrameButton = QPushButton(self.centralwidget)
        self.prevFrameButton.setObjectName(u"prevFrameButton")
        self.prevFrameButton.setEnabled(False)
        self.prevFrameButton.setMinimumSize(QSize(80, 0))
        self.prevFrameButton.setMaximumSize(QSize(80, 16777215))

        self.gridLayout.addWidget(self.prevFrameButton, 2, 0, 1, 1)

        self.seekValue = QLineEdit(self.centralwidget)
        self.seekValue.setObjectName(u"seekValue")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.seekValue.sizePolicy().hasHeightForWidth())
        self.seekValue.setSizePolicy(sizePolicy)
        self.seekValue.setMinimumSize(QSize(0, 0))
        self.seekValue.setMaximumSize(QSize(16777215, 16777215))
        self.seekValue.setMaxLength(30)
        self.seekValue.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.seekValue, 3, 0, 1, 2)

        self.playPauseButton = QPushButton(self.centralwidget)
        self.playPauseButton.setObjectName(u"playPauseButton")
        self.playPauseButton.setEnabled(False)

        self.gridLayout.addWidget(self.playPauseButton, 2, 1, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout)

        self.toolBox = QToolBox(self.centralwidget)
        self.toolBox.setObjectName(u"toolBox")
        self.toolBox.setMinimumSize(QSize(200, 0))
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.page.setGeometry(QRect(0, 0, 266, 402))
        self.verticalLayout_2 = QVBoxLayout(self.page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.scrollArea_2 = QScrollArea(self.page)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 260, 188))
        self.verticalLayout_7 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.keyPointList = QVBoxLayout()
        self.keyPointList.setSpacing(0)
        self.keyPointList.setObjectName(u"keyPointList")

        self.verticalLayout_7.addLayout(self.keyPointList)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_4.addWidget(self.scrollArea_2)

        self.horizontalSpacer = QSpacerItem(40, 5, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.verticalLayout_4.addItem(self.horizontalSpacer)

        self.scrollArea_3 = QScrollArea(self.page)
        self.scrollArea_3.setObjectName(u"scrollArea_3")
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 260, 187))
        self.verticalLayout_8 = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.activityList = QVBoxLayout()
        self.activityList.setSpacing(0)
        self.activityList.setObjectName(u"activityList")

        self.verticalLayout_8.addLayout(self.activityList)

        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout_4.addWidget(self.scrollArea_3)


        self.verticalLayout_2.addLayout(self.verticalLayout_4)

        self.toolBox.addItem(self.page, u"Annotation")
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.page_2.setGeometry(QRect(0, 0, 266, 402))
        self.verticalLayout_5 = QVBoxLayout(self.page_2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(self.page_2)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.interpolationList = QWidget()
        self.interpolationList.setObjectName(u"interpolationList")
        self.interpolationList.setGeometry(QRect(0, 0, 262, 252))
        self.verticalLayout_6 = QVBoxLayout(self.interpolationList)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.interpKeypointList = QListWidget(self.interpolationList)
        self.interpKeypointList.setObjectName(u"interpKeypointList")

        self.verticalLayout_6.addWidget(self.interpKeypointList)

        self.scrollArea.setWidget(self.interpolationList)

        self.verticalLayout_5.addWidget(self.scrollArea)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.interpolateButton = QPushButton(self.page_2)
        self.interpolateButton.setObjectName(u"interpolateButton")

        self.gridLayout_2.addWidget(self.interpolateButton, 3, 0, 1, 2)

        self.label = QLabel(self.page_2)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)

        self.interpInitialIndex = QLabel(self.page_2)
        self.interpInitialIndex.setObjectName(u"interpInitialIndex")
        self.interpInitialIndex.setAlignment(Qt.AlignCenter)

        self.gridLayout_2.addWidget(self.interpInitialIndex, 1, 1, 1, 1)

        self.interpSetCurrentIndex = QPushButton(self.page_2)
        self.interpSetCurrentIndex.setObjectName(u"interpSetCurrentIndex")

        self.gridLayout_2.addWidget(self.interpSetCurrentIndex, 2, 0, 1, 2)

        self.interpSelectAllButton = QPushButton(self.page_2)
        self.interpSelectAllButton.setObjectName(u"interpSelectAllButton")

        self.gridLayout_2.addWidget(self.interpSelectAllButton, 0, 0, 1, 1)

        self.interpClearAllButton = QPushButton(self.page_2)
        self.interpClearAllButton.setObjectName(u"interpClearAllButton")

        self.gridLayout_2.addWidget(self.interpClearAllButton, 0, 1, 1, 1)


        self.verticalLayout_5.addLayout(self.gridLayout_2)

        self.verticalLayout_5.setStretch(0, 2)
        self.verticalLayout_5.setStretch(1, 1)
        self.toolBox.addItem(self.page_2, u"Interpolation")

        self.verticalLayout_3.addWidget(self.toolBox)


        self.gridLayout_3.addLayout(self.verticalLayout_3, 1, 1, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.viewTabWidget = QTabWidget(self.centralwidget)
        self.viewTabWidget.setObjectName(u"viewTabWidget")

        self.verticalLayout.addWidget(self.viewTabWidget)


        self.gridLayout_3.addLayout(self.verticalLayout, 1, 0, 1, 1)

        self.seekBar = QSlider(self.centralwidget)
        self.seekBar.setObjectName(u"seekBar")
        self.seekBar.setOrientation(Qt.Horizontal)

        self.gridLayout_3.addWidget(self.seekBar, 2, 0, 1, 2)

        self.gridLayout_3.setColumnStretch(0, 5)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1280, 30))
        self.menuProject = QMenu(self.menubar)
        self.menuProject.setObjectName(u"menuProject")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuProject.menuAction())
        self.menuProject.addAction(self.actionNew)
        self.menuProject.addAction(self.actionLoad)
        self.menuProject.addAction(self.actionSave)

        self.retranslateUi(MainWindow)

        self.toolBox.setCurrentIndex(0)
        self.toolBox.layout().setSpacing(6)
        self.viewTabWidget.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"New", None))
#if QT_CONFIG(shortcut)
        self.actionNew.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
        self.actionLoad.setText(QCoreApplication.translate("MainWindow", u"Open", None))
#if QT_CONFIG(shortcut)
        self.actionLoad.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
#if QT_CONFIG(shortcut)
        self.actionSave.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.frameNumber.setText(QCoreApplication.translate("MainWindow", u"Frame-Number :", None))
        self.seekButton.setText(QCoreApplication.translate("MainWindow", u"Seek", None))
        self.nextFrameButton.setText(QCoreApplication.translate("MainWindow", u"Next", None))
#if QT_CONFIG(shortcut)
        self.nextFrameButton.setShortcut(QCoreApplication.translate("MainWindow", u"Right", None))
#endif // QT_CONFIG(shortcut)
        self.resetViewButton.setText(QCoreApplication.translate("MainWindow", u"Reset View", None))
        self.prevFrameButton.setText(QCoreApplication.translate("MainWindow", u"Prev", None))
#if QT_CONFIG(shortcut)
        self.prevFrameButton.setShortcut(QCoreApplication.translate("MainWindow", u"Left", None))
#endif // QT_CONFIG(shortcut)
        self.seekValue.setInputMask(QCoreApplication.translate("MainWindow", u"999999999999999999999999999999", None))
        self.playPauseButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), QCoreApplication.translate("MainWindow", u"Annotation", None))
        self.interpolateButton.setText(QCoreApplication.translate("MainWindow", u"Interpolate", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Initial Index", None))
        self.interpInitialIndex.setText("")
        self.interpSetCurrentIndex.setText(QCoreApplication.translate("MainWindow", u"Update Index", None))
        self.interpSelectAllButton.setText(QCoreApplication.translate("MainWindow", u"Select All", None))
        self.interpClearAllButton.setText(QCoreApplication.translate("MainWindow", u"Clear All", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QCoreApplication.translate("MainWindow", u"Interpolation", None))
        self.menuProject.setTitle(QCoreApplication.translate("MainWindow", u"Project", None))
    # retranslateUi

