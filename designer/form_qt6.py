from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(670, 117)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")


        # Horizontal layout for source field and min length
        self.horizontalLayout_1 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_1.setObjectName("horizontalLayout_1")

        self.label = QtWidgets.QLabel(parent=Dialog)
        self.label.setObjectName("label")
        self.horizontalLayout_1.addWidget(self.label)

        self.srcField = QtWidgets.QComboBox(parent=Dialog)
        self.srcField.setMinimumSize(QtCore.QSize(120, 0))
        self.srcField.setObjectName("srcField")
        self.horizontalLayout_1.addWidget(self.srcField)

        self.minLengthLabel = QtWidgets.QLabel(parent=Dialog)
        self.minLengthLabel.setObjectName("minLengthLabel")
        self.minLengthLabel.setText("Min Char Length:")
        self.horizontalLayout_1.addWidget(self.minLengthLabel)

        self.minLengthField = QtWidgets.QSpinBox(parent=Dialog)
        self.minLengthField.setObjectName("minLengthField")
        self.minLengthField.setMinimumSize(QtCore.QSize(60, 0))
        self.minLengthField.setMinimum(0)  # Set minimum value
        self.minLengthField.setMaximum(999)  # Set maximum value
        self.horizontalLayout_1.addWidget(self.minLengthField)

        # Add the horizontal layout to the main vertical layout
        self.verticalLayout.addLayout(self.horizontalLayout_1)

        self.horizontalLayout_check = QtWidgets.QHBoxLayout()
        self.horizontalLayout_check.setObjectName("horizontalLayout_check")

        self.exactSearchCheckBox = QtWidgets.QCheckBox(parent=Dialog)
        self.exactSearchCheckBox.setObjectName("exactSearchCheckBox")
        self.exactSearchCheckBox.setText("Exact Search")
        self.horizontalLayout_check.addWidget(self.exactSearchCheckBox)

        self.highlightingCheckBox = QtWidgets.QCheckBox(parent=Dialog)
        self.highlightingCheckBox.setObjectName("highlightingCheckBox")
        self.highlightingCheckBox.setText("Sentence Highlighting")
        self.horizontalLayout_check.addWidget(self.highlightingCheckBox)

        self.sourceMediaTagCheckBox = QtWidgets.QCheckBox(parent=Dialog)
        self.sourceMediaTagCheckBox.setObjectName("sourceMediaTagCheckBox")
        self.sourceMediaTagCheckBox.setText("Tag With Source Media")
        self.horizontalLayout_check.addWidget(self.sourceMediaTagCheckBox)

        self.mergeCheckbox = QtWidgets.QCheckBox(parent=Dialog)
        self.mergeCheckbox.setObjectName("mergeCheckbox")
        self.mergeCheckbox.setText("Merge with prev and next sentence")
        self.horizontalLayout_check.addWidget(self.mergeCheckbox)

        self.verticalLayout.addLayout(self.horizontalLayout_check)

        # Add line
        self.line = QtWidgets.QFrame(parent=Dialog)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        
        self.verticalLayout.addLayout(self.gridLayout)
        
        
        self.line_2 = QtWidgets.QFrame(parent=Dialog)
        self.line_2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line_2.setObjectName("line_2")
        self.verticalLayout.addWidget(self.line_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.pushButton = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Dialog)
        self.pushButton.clicked.connect(Dialog.accept) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Batch Download"))
        self.label.setText(_translate("Dialog", "Source Field:"))
        self.pushButton.setText(_translate("Dialog", "Start"))
        self.minLengthLabel.setText(_translate("Dialog", "Min Char Length:"))
