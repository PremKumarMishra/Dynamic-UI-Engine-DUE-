from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import xml.etree.ElementTree as ET
import functools
import textwrap
import random
from DUE.cwidgets import *
from DUE.effects import *
#from QAcrylic import WindowEffect
import DUE.utils.Resource

class Engine:
    WIDGET_REGISTRY = {}
    RESOURCE = {}

    def __init__(self,default_size:tuple):
        self.window = QMainWindow()
        self.window.setFixedSize(default_size[0],default_size[1])

        self.body = QFrame(self.window)
        self.body.setObjectName("body")
        self.window.setCentralWidget(self.body)

        #Update Function Registry
        globals()["document"] = self
        
        #Initialise Audio Engine
        Audio.audio_init()

    def load(self,src:str):
        self.dom_tree = ET.parse(src)
        self.root = self.dom_tree.getroot()
    
        #Set Window Attributes
        for win_attrb in self.root.attrib.items():
            self.parseWindowAttributes(win_attrb)
        
        #Set Main Window Layout
        for content in self.root.findall("./"):
            match content.tag:
                case "layout":
                    t= time.time()
                    self.parseLayout(self.body,content)
                case "script":
                    exec(textwrap.dedent(content.text),globals())
                case "audio":
                    self.parseAudio(content)
                case "widget":
                    self.parseWidget(None,content)
                case "effect":
                    self.parseGraphicsEffect(content)
                case "animation":
                    self.parseAnimation(content)
                case "timer":
                    self.parseTimer(content)
                case "loader":
                    self.parseFontLoader(content)
                case "style":
                    self.window.setStyleSheet(content.text)

        return self.window

    #Bind Dynamic Event Functions
    def bindDynamicEvent(self,func_name,*args):
        func =  globals().get(func_name)
        if args and not args[0]:
            args = ()
        if func:
            if args:
                func(*args)
            else:
                func()

    #Register Function
    def registerFunction(self,func_name,func):
        if func_name not in globals():
            globals()[func_name] = func
    
    #Unregister Function
    def unregisterFunction(self,func_name,func):
        if func_name in globals():
            del globals()[func_name]
    
    def parseWindowAttributes(self,win_attrb:tuple):
        match win_attrb[0]:
            case "id":
                self.window.setObjectName(win_attrb[1])
                self.WIDGET_REGISTRY[win_attrb[1]] = self.window
            case "width":
                self.window.setFixedWidth(int(win_attrb[1]))
            case "height":
                self.window.setFixedHeight(int(win_attrb[1]))
            case "title":
                self.window.setWindowTitle(win_attrb[1])
            case "icon":
                self.window.setWindowIcon(QIcon(win_attrb[1]))
            case "material":
                if win_attrb[1] == "acrylic":
                    win_effect = WindowEffect()
                    win_effect.setAcrylicEffect(int(self.window.winId()))
                    del win_effect
                elif win_attrb[1] == "aero":
                    win_effect = WindowEffect()
                    win_effect.setAeroEffect(int(self.window.winId()))
                    del win_effect
            case "flags":
                flags = [self.getWindowTypeByName(flag) for flag in win_attrb[1].split("|")]
                for flag in flags:
                    self.window.setWindowFlag(flag)
                # del flags
            case "attribute":
                self.window.setAttribute(self.getWidgetAttributeByName(win_attrb[1]))

    def parseLayout(self,parent:QWidget,layout:ET.Element):
        Layout = None
        #Setup Layout Attributes
        for layout_attrb in layout.items():
            match layout_attrb[0]:
                case "type":
                    if layout_attrb[1] == "vbox":
                        Layout = QVBoxLayout()
                    elif layout_attrb[1] == "hbox":
                        Layout = QHBoxLayout()
                    elif layout_attrb[1] == "grid":
                        Layout = QGridLayout()
                case "id":
                    Layout.setObjectName(layout_attrb[1])
                    self.WIDGET_REGISTRY[layout_attrb[1]] = Layout
                case "margin":
                    Layout.setContentsMargins(*[int(margin) for margin in layout_attrb[1].split(" ")])
                case "spacing":
                    Layout.setSpacing(int(layout_attrb[1]))
                case "alignment":
                    Layout.setAlignment(self.getAlignmentByName(layout_attrb[1]))
        
        #Setup Layout Content
        for content in layout.findall("./"):
            match content.tag:
                case "button":
                    self.parseButton(Layout,content)
                case "label":
                    self.parseLabel(Layout,content)
                case "frame":
                    self.parseFrame(Layout,content)
                case "image":
                    self.parseImage(Layout,content)
                case "audio":
                    self.parseAudio(content)
                case "checkbox":
                    self.parseCheckbox(Layout,content)
                case "combobox":
                    self.parseCombobox(Layout,content)
                case "datetime":
                    self.parseDateTime(Layout,content)
                case "slider":
                    self.parseSlider(Layout,content)
                case "cslider":
                    self.parseCSlider(Layout,content)
                case "switch":
                    self.parseSwitch(Layout,content)
                case "dial":
                    self.parseDial(Layout,content)
                case "spinbox":
                    self.parseSpinBox(Layout,content)
                case "lcd":
                    self.parseLcdNumber(Layout,content)
                case "input":
                    self.parseLineEdit(Layout,content)
                case "progressbar":
                    self.parseProgressBar(Layout,content)
                case "radiobutton":
                    self.parseRadioButton(Layout,content)
                case "scrollarea":
                    self.parseScrollArea(Layout,content)
                case "sizegrip":
                    self.parseSizeGrip(Layout,content)
                case "tabbar":
                    self.parseTabBar(Layout,content)
                case "textedit":
                    self.parseTextEdit(Layout,content)
                case "tabwidget":
                    self.parseTabWidget(Layout,content)
                case "toolbox":
                    self.parseToolBox(Layout,content)
                case "widget":
                    self.parseWidget(Layout,content)
                case "space":
                    Layout.addSpacing(int(content.text))
                case "stretch":
                    Layout.addStretch(int(content.text))
                case "effect":
                    self.parseGraphicsEffect(content)
                case "animation":
                    self.parseAnimation(content)

        #Add Spacing To Layout If Provided
        # for content in layout.findall("./"):
        #     print(content.tag)
        #     if content.tag == "space":
        #         Layout.addSpacing(int(content.text))
        #     elif content.tag =="stretch":
        #         Layout.addStretch(int(content.text))
        
        parent.setLayout(Layout)

    def parseMenu(self,parent:QWidget,menu:ET.Element):
        Menu = QMenu(parent)
        Menu.setTitle(menu.text)
        for menu_attrb in menu.items():
            match menu_attrb[0]:
                case "tear-off-enabled":
                    Menu.setTearOffEnabled(eval(menu_attrb[1]))
                case "tool-tips-visible":
                    Menu.setToolTipsVisible(eval(menu_attrb[1]))
                case "tooltip":
                    Menu.setToolTip(menu_attrb[1])
                case "tool-tip-duration":
                    Menu.setToolTipDuration(int(menu_attrb[1]))
                case "icon":
                    Menu.setIcon(QIcon(menu_attrb[1]))
        
        for content in menu.findall("./"):
            if content.tag == "menu":
                Menu.addMenu(self.parseMenu(Menu,content))
            elif content.tag == "section":
                self.parseSection(Menu,content)
            elif content.tag == "sep":
                Menu.addSeparator() #ADD QACTION
            elif content.tag == "action":
                Menu.addAction(content.text)

        return Menu

    def parseSection(self,menu:QMenu,section:ET.Element):
        icon =  QIcon()
        for section_attrb in section.items():
            match section_attrb[0]:
                case "icon":
                    icon = QIcon(section_attrb[1])
        menu.addSection(icon,section.text) #ADD QACTION

    def parseComboboxValue(self,box:QComboBox,value:ET.Element):
        icon = None
        text = value.text
        userdata = None
        for value_attrbs in value.items():
            if value_attrbs[0] == "icon":
                icon = QIcon(value_attrbs[1])
            elif value_attrbs[0] == "data":
                userdata = value_attrbs[1]
        if icon:
            box.addItem(icon,text,userdata)
        else:
            box.addItem(text,userdata)

    def parseButton(self,layout:QLayout,widget:ET.Element):
        element = QPushButton(widget.text,self.body)
        anchor = None
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "anchor":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        anchor = flag1|flag2
                        del flag
                    else:
                        anchor = self.getAlignmentByName(button_attrb[1])
                case "flat":
                    element.setFlat(eval(button_attrb[1]))
                case "icon":
                    element.setIcon(QIcon(self.loadResourceByName(button_attrb[1])))
                case "icon-size":
                    size = [int(size) for size in button_attrb[1].split(" ")]
                    element.setIconSize(QSize(*size))
                    del size
                case "auto_default":
                    element.setAutoDefault(eval(button_attrb[1]))
                case "default":
                    element.setDefault(eval(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onClick":
                    element.clicked.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        #Add Menu If Provided
        for content in widget.findall("./"):
            if content.tag == "menu":
                element.setMenu(self.parseMenu(element,content))
        
        if not anchor:
            layout.addWidget(element)
        else:
            layout.addWidget(element,alignment=anchor)

    def parseCommandLinkButton(self,layout:QLayout,widget:ET.Element):
        element = QCommandLinkButton(widget.text,self.body)
        anchor = None
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "anchor":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        anchor = flag1|flag2
                        del flag
                    else:
                        anchor = self.getAlignmentByName(button_attrb[1])
                case "flat":
                    element.setFlat(eval(button_attrb[1]))
                case "icon":
                    element.setIcon(QIcon(button_attrb[1]))
                case "icon-size":
                    size = [int(size) for size in button_attrb[1].split(" ")]
                    element.setIconSize(QSize(*size))
                    del size
                case "auto_default":
                    element.setAutoDefault(eval(button_attrb[1]))
                case "default":
                    element.setDefault(eval(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onClick":
                    element.clicked.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
                

        #Add Menu If Provided
        for content in widget.findall("./"):
            if content.tag == "menu":
                element.setMenu(self.parseMenu(element,content))
        
        if not anchor:
            layout.addWidget(element)
        else:
            layout.addWidget(element,alignment=anchor)

    def parseLabel(self,layout:QLayout,widget:ET.Element):
        element = QLabel(widget.text,self.body)
        anchor = None
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "anchor":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        anchor = flag1|flag2
                        del flag
                    else:
                        anchor = self.getAlignmentByName(button_attrb[1])
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "open-links":
                    element.setOpenExternalLinks(eval(button_attrb[1]))
                case "margin":
                    element.setMargin(int(button_attrb[1]))
                case "indent":
                    element.setIndent(int(button_attrb[1]))
                case "word-wrap":
                    element.setWordWrap(eval(button_attrb[1]))
                case "scaled-contents":
                    element.setScaledContents(eval(button_attrb[1]))
                case "text-interaction-flags":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getTextInteractionFlagByName(flag[0])
                        flag2 = self.getTextInteractionFlagByName(flag[1])
                        element.setTextInteractionFlags(flag1|flag2)
                        del flag
                    else:
                        element.setTextInteractionFlags(button_attrb[1])
                case "text-format":
                    element.setTextFormat(self.getTextFormatByName(button_attrb[1]))
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "alignment":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        element.setAlignment(flag1|flag2)
                        del flag
                    else:
                        element.setAlignment(self.getAlignmentByName(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)


        if not anchor:
            layout.addWidget(element)
        else:
            layout.addWidget(element,alignment=anchor)

    def parseFrame(self,layout:QLayout,widget:ET.Element):
        element = QFrame(self.body)
        anchor = None
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])                    
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "anchor":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        anchor = flag1|flag2
                        del flag
                    else:
                        anchor = self.getAlignmentByName(button_attrb[1])
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
        
        #Add Frame Layout If Provided
        for content in widget.findall("./"):
            if content.tag == "layout":
                self.parseLayout(element,content)
        
        if layout == None:
            return element
        
        if not anchor:
            layout.addWidget(element)
        else:
            layout.addWidget(element,alignment=anchor)

    def parseImage(self,layout:QLayout,widget:ET.Element):
        element = Image(self.body)
        anchor = None
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "radius":
                    element.setRadius(int(button_attrb[1]))
                case "antialiasing":
                    element.setAntialiasing(bool(button_attrb[1]))
                case "src":
                    element.drawPixmap(button_attrb[1])
                case "alt":
                    element.setAlternative(button_attrb[1])
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "anchor":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        anchor = flag1|flag2
                        del flag
                    else:
                        anchor = self.getAlignmentByName(button_attrb[1])
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
                case "alignment":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        element.setAlignment(flag1|flag2)
                        del flag
                    else:
                        element.setAlignment(button_attrb[1])
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
        
        if not anchor:
            layout.addWidget(element)
        else:
            layout.addWidget(element,alignment=anchor)

    def parseCheckbox(self,layout:QLayout,widget:ET.Element):
        element = QCheckBox()
        element.setText(widget.text)
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "tri-state":
                    element.setTristate(eval(button_attrb[1]))
                case "state":
                    element.setCheckState(self.getCheckStateByName(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "onClick":
                    element.clicked.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseCombobox(self,layout:QLayout,widget:ET.Element):
        element = QComboBox()
        element.setCurrentText(widget.text.strip())
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "duplicates":
                    element.setDuplicatesEnabled(eval(button_attrb[1]))
                case "editable":
                    element.setEditable(eval(button_attrb[1]))
                case "frame":
                    element.setFrame(eval(button_attrb[1]))
                case "icon-size":
                    size = button_attrb[1].split(" ")
                    element.setIconSize(QSize(int(size[0]),int(size[1])))
                    del size
                case "placeholder":
                    element.setPlaceholderText(button_attrb[1])
                case "max-count":
                    element.setMaxCount(int(button_attrb[1]))
                case "max-visible":
                    element.setMaxVisibleItems(int(button_attrb[1]))
                case "current-text":
                    element.setCurrentText(button_attrb[1])
                case "current-index":
                    element.setCurrentIndex(int(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        #Add Values If Provided
        for content in widget.findall("./"):
            if content.tag == "value":
                self.parseComboboxValue(element,content)
        
        layout.addWidget(element)

    def parseDateTime(self,layout:QLayout,widget:ET.Element):
        element = QDateTimeEdit()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "frame":
                    element.setFrame(eval(button_attrb[1]))
                case "calender-popup":
                    element.setCalendarPopup(eval(button_attrb[1]))
                case "max-date":
                    date = [int(date) for date in button_attrb[1].split("-")]
                    element.setMaximumDate(QDate(*date))
                case "min-date":
                    date = [int(date) for date in button_attrb[1].split("-")]
                    element.setMinimumDate(QDate(*date))
                case "date-range":
                    date = button_attrb[1].split(" ")
                    element.setDateRange(QDate(*date[0].split("-")),QDate(*date[1].split("-")))
                case "max-time":
                    time = [int(time) for time in button_attrb[1].split(":")]
                    element.setMaximumTime(QTime(*time))
                case "min-time":
                    time = [int(time) for time in button_attrb[1].split(":")]
                    element.setMinimumTime(QTime(*time))
                case "time-range":
                    Time = button_attrb[1].split(" ")
                    element.setTimeRange(QTime(*Time[0].split(":")),QTime(*Time[1].split(":")))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseSlider(self,layout:QLayout,widget:ET.Element):
        element = QSlider()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "type":
                    if button_attrb[1] == "vertical":
                        element.setOrientation(Qt.Orientation.Vertical)
                    else:
                        element.setOrientation(Qt.Orientation.Horizontal)
                case "interval":
                    element.setTickInterval(int(button_attrb[1]))
                case "value":
                    element.setValue(int(button_attrb[1]))
                case "range":
                    element.setRange(*[int(val) for val in button_attrb[1].split("-")])
                case "position":
                    element.setTickPosition(self.getAlignmentByName(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onValueChange":
                    element.valueChanged.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)
    
    def parseCSlider(self,layout:QLayout,widget:ET.Element):
        element = CSlider()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "type":
                    if button_attrb[1] == "vertical":
                        element.setOrientation(Qt.Orientation.Vertical)
                    else:
                        element.setOrientation(Qt.Orientation.Horizontal)
                case "value":
                    element.setValue(int(button_attrb[1]))
                case "range":
                    element.setRange(*[int(val) for val in button_attrb[1].split("-")])
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onValueChange":
                    element.valueChanged.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseSwitch(self,layout:QLayout,widget:ET.Element):
        element = QSwitch()
        anchor = None
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "anchor":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        anchor = flag1|flag2
                        del flag
                    else:
                        anchor = self.getAlignmentByName(button_attrb[1])
                case "icon":
                    element.setIcon(QIcon(button_attrb[1]))
                case "icon-size":
                    size = [int(size) for size in button_attrb[1].split(" ")]
                    element.setIconSize(QSize(*size))
                    del size
                case "checked":
                    element.setChecked(eval(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onSwitch":
                    element.switched.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
        
        if not anchor:
            layout.addWidget(element)
        else:
            layout.addWidget(element,alignment=anchor)

    def parseDial(self,layout:QLayout,widget:ET.Element):
        element = QDial()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "type":
                    if button_attrb[1] == "vertical":
                        element.setOrientation(Qt.Orientation.Vertical)
                    else:
                        element.setOrientation(Qt.Orientation.Horizontal)
                case "notch-target":
                    element.setNotchTarget(float(button_attrb[1]))
                case "notch-visible":
                    element.setNotchesVisible(bool(button_attrb[1]))
                case "wrapping":
                    element.setWrapping(bool(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseSpinBox(self,layout:QLayout,widget:ET.Element):
        element = None
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "type":
                    if button_attrb[1] == "single":
                        element = QSpinBox()
                    else:
                        element = QDoubleSpinBox()
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "decimals":
                    if hasattr(element,"decimals"):
                        element.setDecimals(int(button_attrb[1]))
                case "int-base":
                    if hasattr(element,"displayIntegerBase"):
                        element.setDisplayIntegerBase(int(button_attrb[1]))
                case "max":
                    element.setMaximum(float(button_attrb[1]))
                case "min":
                    element.setMinimum(float(button_attrb[1]))
                case "prefix":
                    element.setPrefix(button_attrb[1])
                case "suffix":
                    element.setSuffix(button_attrb[1])
                case "value":
                    element.setValue(int(button_attrb[1]))
                case "step":
                    element.setSingleStep(self.getStepTypeByName(button_attrb[1]))
                case "wrapping":
                    element.setWrapping(bool(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseLcdNumber(self,layout:QLayout,widget:ET.Element):
        element = QLCDNumber()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "small-dec-point":
                    element.setSmallDecimalPoint(bool(button_attrb[1]))
                case "count":
                    element.setDigitCount(int(button_attrb[1]))
                case "mode":
                    element.setMode(self.getLCDModeByName(button_attrb[1]))
                case "segment":
                    element.setSegmentStyle(self.getLCDSegmentByName(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseLineEdit(self,layout:QLayout,widget:ET.Element):
        element = QLineEdit()
        element.setText(widget.text)
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "alignment":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        element.setAlignment(flag1|flag2)
                        del flag
                    else:
                        element.setAlignment(button_attrb[1])
                case "frame":
                    element.setFrame(eval(button_attrb[1]))
                case "placeholder":
                    element.setPlaceholderText(button_attrb[1])
                case "max-length":
                    element.setMaxLength(int(button_attrb[1]))
                case "clear-button":
                    element.setClearButtonEnabled(bool(button_attrb[1]))
                case "cursor-pos":
                    element.setCursorPosition(int(button_attrb[1]))
                case "drag-enable":
                    element.setDragEnabled(bool(button_attrb[1]))
                case "input-mask":
                    element.setInputMask(button_attrb[1])
                case "modified":
                    element.setModified(bool(button_attrb[1]))
                case "read-only":
                    element.setReadOnly(bool(button_attrb[1]))
                case "margins":
                    margin = [int(margin) for margin in button_attrb[1].split(" ")]
                    element.setTextMargins(*margin)
                    del margin
                case "echo-mode":
                    element.setEchoMode(self.getEchoModeByName(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseProgressBar(self,layout:QLayout,widget:ET.Element):
        element = QProgressBar()
        element.setFormat(widget.text)
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "alignment":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        element.setAlignment(flag1|flag2)
                        del flag
                    else:
                        element.setAlignment(self.getAlignmentByName(button_attrb[1]))
                case "type":
                    if button_attrb[1] == "vertical":
                        element.setOrientation(Qt.Orientation.Vertical)
                    elif button_attrb[1] == "horizontal":
                        element.setOrientation(Qt.Orientation.Horizontal)
                case "value":
                    element.setValue(int(button_attrb[1]))
                case "min":
                    element.setMinimum(int(button_attrb[1]))
                case "max":
                    element.setMaximum(int(button_attrb[1]))
                case "text-visible":
                    element.setTextVisible(eval(button_attrb[1]))
                case "text-direction":
                    if button_attrb[1] == "top-to-bottom":
                        element.setTextDirection(QProgressBar.Direction.TopToBottom)
                    else:
                        element.setTextDirection(QProgressBar.Direction.BottomToTop)
                case "inverted":
                    element.setInvertedAppearance(bool(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseRadioButton(self,layout:QLayout,widget:ET.Element):
        element = QRadioButton(widget.text,None)
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "checkable":
                    element.setCheckable(bool(button_attrb[1]))
                case "checked":
                    element.setChecked(bool(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onClick":
                    element.clicked.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseScrollArea(self,layout:QLayout,widget:ET.Element):
        element = QScrollArea()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "alignment":
                    if button_attrb[1].find("|") != -1:
                        flag = button_attrb[1].split("|")
                        flag1 = self.getAlignmentByName(flag[0])
                        flag2 = self.getAlignmentByName(flag[1])
                        element.setAlignment(flag1|flag2)
                        del flag
                    else:
                        element.setAlignment(button_attrb[1])
                case "widget-resize":
                    element.setWidgetResizable(bool(button_attrb[1]))
                case "horizontal-bar-policy":
                    element.setHorizontalScrollBarPolicy(self.getScrollBarPolicyByName(button_attrb[1]))
                case "vertical-bar-policy":
                    element.setVerticalScrollBarPolicy(self.getScrollBarPolicyByName(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onClick":
                    element.clicked.connect(functools.partial(self.bindDynamicEvent,button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        #Add Frame As ScrollArea's Widget  If Provided
        for content in widget.findall("./"):
            if content.tag == "frame":
                element.setWidget(self.parseFrame(None,content))
        
        layout.addWidget(element)

    def parseSizeGrip(self,layout:QLayout,widget:ET.Element):
        element = QSizeGrip(layout)
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        layout.addWidget(element)

    def parseTabBar(self,layout:QLayout|None,widget:ET.Element) -> QTabBar | None:
        element = QTabBar()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "auto-hide":
                    element.setAutoHide(bool(button_attrb[1]))
                case "change-current-on-drag":
                    element.setChangeCurrentOnDrag(bool(button_attrb[1]))
                case "document-mode":
                    element.setDocumentMode(bool(button_attrb[1]))
                case "draw-base":
                    element.setDrawBase(bool(button_attrb[1]))
                case "expanding":
                    element.setExpanding(bool(button_attrb[1]))
                case "movable":
                    element.setMovable(bool(button_attrb[1]))
                case "tabs-closable":
                    element.setTabsClosable(bool(button_attrb[1]))
                case "uses-scroll-button":
                    element.setUsesScrollButtons(bool(button_attrb[1]))
                case "elide-mode":
                    element.setElideMode(self.getElideModeByName(button_attrb[1]))
                case "icon-size":
                    size = [int(size) for size in button_attrb[1].split(" ")]
                    element.setIconSize(QSize(*size))
                    del size
                case "sel-behaviour-on-remove":
                    element.setSelectionBehaviorOnRemove(self.getSelectionBehaviourByName(button_attrb[1]))
                case "shape":
                    element.setShape(self.getTabBarShapeByName(button_attrb[1]))
                case "current-index":
                    element.setCurrentIndex(int(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)

        #Add Tabs If Provided
        for content in widget.findall("./"):
            if content.tag == "tab":
                self.parseTabs(element,content)

        if not layout:
            return element
        layout.addWidget(element)

    def parseTabWidget(self,layout:QLayout,widget:ET.Element):
        element = QTabWidget()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "tab-auto-hide":
                    element.setTabBarAutoHide(bool(button_attrb[1]))
                case "tab-position":
                    element.setTabPosition(self.getTabPositionByName(button_attrb[1]))
                case "document-mode":
                    element.setDocumentMode(bool(button_attrb[1]))
                case "movable":
                    element.setMovable(bool(button_attrb[1]))
                case "tabs-closable":
                    element.setTabsClosable(bool(button_attrb[1]))
                case "uses-scroll-button":
                    element.setUsesScrollButtons(bool(button_attrb[1]))
                case "elide-mode":
                    element.setElideMode(self.getElideModeByName(button_attrb[1]))
                case "icon-size":
                    size = [int(size) for size in button_attrb[1].split(" ")]
                    element.setIconSize(QSize(*size))
                    del size
                case "tab-shape":
                    element.setTabShape(self.getTabBarShapeByName(button_attrb[1]))
                case "current-index":
                    element.setCurrentIndex(int(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
        
        #Add Tabs If Provided
        for content in widget.findall("./"):
            if content.tag == "tab":
                self.parseTabs(element,content)
            elif content.tag == "tabbar":
                element.setTabBar(self.parseTabBar(None,content))

        layout.addWidget(element)
    
    def parseTabs(self,element:QTabBar|QTabWidget|QToolBox,content:ET.Element):
        icon = content.get("icon")
        widget = None
        
        for sub_content in content.findall("./"):
            if sub_content.tag == "frame":
                widget = self.parseFrame(None,sub_content)
                break

        if icon:
            if widget != None:
                if hasattr(element,"addTab"):
                    element.addTab(widget,icon,content.text)
                else:
                    element.addItem(widget,icon,content.text)
            else:
                element.addTab(icon,content.text)
        else:
            if widget != None:
                if hasattr(element,"addTab"):
                    element.addTab(widget,content.text)
                else:
                    element.addItem(widget,content.text)
            else:
                element.addTab(content.text)

    def parseTextEdit(self,layout:QLayout,widget:ET.Element):
        element = QTextEdit()
        for text_attrb in widget.items():
            match text_attrb[0]:
                case "id":
                    element.setObjectName(text_attrb[1])
                    self.WIDGET_REGISTRY[text_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(text_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(text_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(text_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(text_attrb[1]))
                case "width":
                    element.setFixedWidth(int(text_attrb[1]))
                case "height":
                    element.setFixedHeight(int(text_attrb[1]))
                case "accept-rich-text":
                    element.setAcceptRichText(eval(text_attrb[1]))
                case "overwrite-mode":
                    element.setOverwriteMode(eval(text_attrb[1]))
                case "tab-changes-focus":
                    element.setTabChangesFocus(eval(text_attrb[1]))
                case "undo-redo-enabled":
                    element.setUndoRedoEnabled(eval(text_attrb[1]))
                case "read-only":
                    element.setReadOnly(eval(text_attrb[1]))
                case "placeholder":
                    element.setPlaceholderText(text_attrb[1])
                case "cursor-width":
                    element.setCursorWidth(int(text_attrb[1]))
                case "line-wrap-column-or-width":
                    element.setLineWrapColumnOrWidth(int(text_attrb[1]))
                case "line-wrap-mode":
                    element.setLineWrapColumnOrWidth(self.getLineWrapModeByName(text_attrb[1]))
                case "word-wrap-mode":
                    element.setWordWrapMode(self.getWordWrapModeByName(text_attrb[1]))
                case "text-interaction-flags":
                    if text_attrb[1].find("|") != -1:
                        flag = text_attrb[1].split("|")
                        flag1 = self.getTextInteractionFlagByName(flag[0])
                        flag2 = self.getTextInteractionFlagByName(flag[1])
                        element.setTextInteractionFlags(flag1|flag2)
                        del flag
                    else:
                        element.setTextInteractionFlags(text_attrb[1])
                case "horizontal-bar-policy":
                    element.setHorizontalScrollBarPolicy(self.getScrollBarPolicyByName(text_attrb[1]))
                case "vertical-bar-policy":
                    element.setVerticalScrollBarPolicy(self.getScrollBarPolicyByName(text_attrb[1]))
                case "size-policy":
                    policy = text_attrb[1].split(" ")
                    element.setSizePolicy(self.getSizePolicyByName(policy[0]),self.getSizePolicyByName(policy[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(text_attrb[1]))
                case "tooltip":
                    element.setToolTip(text_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(text_attrb[1]))
                case "visible":
                    element.setVisible(eval(text_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,text_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,text_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,text_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,text_attrb[1])
                case "style":
                    element.setStyleSheet(text_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(text_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(text_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
        layout.addWidget(element)

    def parseToolBox(self,layout:QLayout,widget:ET.Element):
        element = QToolBox()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "current-index":
                    element.setCurrentIndex(int(button_attrb[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "tooltip":
                    element.setToolTip(button_attrb[1])
                case "tool-tip-duration":
                    element.setToolTipDuration(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
        
        #Add Tabs If Provided
        for content in widget.findall("./"):
            if content.tag == "tab":
                self.parseTabs(element,content)

        layout.addWidget(element)

    def parseWidget(self,layout:QLayout,widget:ET.Element):
        element = QWidget()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    element.setObjectName(button_attrb[1])
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "flags":
                    flags = [self.getWindowTypeByName(flag) for flag in button_attrb[1].split("|")]
                    for flag in flags:
                        element.setWindowFlag(flag)
                case "attrbute":
                    element.setAttribute(self.getWidgetAttributeByName(button_attrb[1]))
                case "min-width":
                    element.setMinimumWidth(int(button_attrb[1]))
                case "min-height":
                    element.setMinimumHeight(int(button_attrb[1]))
                case "max-width":
                    element.setMaximumWidth(int(button_attrb[1]))
                case "max-height":
                    element.setMaximumHeight(int(button_attrb[1]))
                case "width":
                    element.setFixedWidth(int(button_attrb[1]))
                case "height":
                    element.setFixedHeight(int(button_attrb[1]))
                case "visible":
                    element.setVisible(eval(button_attrb[1]))
                case "size-policy":
                    policy = button_attrb[1].split(" ")
                    element.setSizePolicy(self.getSizePolicyByName(policy[0]),self.getSizePolicyByName(policy[1]))
                case "cursor":
                    element.setCursor(self.getCursorShapeByName(button_attrb[1]))
                case "style":
                    element.setStyleSheet(button_attrb[1])
                case "effect":
                    effect = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if effect:
                        element.setGraphicsEffect(effect)
                case "anim":
                    animation = self.WIDGET_REGISTRY.get(button_attrb[1])
                    if animation:
                        animation.setTargetObject(element)
                case "onMouseMove":
                    element.mouseMoveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMousePress":
                    element.mousePressEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseEnter":
                    element.enterEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
                case "onMouseLeave":
                    element.leaveEvent = functools.partial(self.bindDynamicEvent,button_attrb[1])
        
        #Add Frame Layout If Provided
        for content in widget.findall("./"):
            if content.tag == "layout":
                self.parseLayout(element,content)
        
        if not layout:
            return element
        layout.addWidget(element)

    def parseAudio(self,widget:ET.Element):
        element = Audio()
        for button_attrb in widget.items():
            match button_attrb[0]:
                case "id":
                    self.WIDGET_REGISTRY[button_attrb[1]] = element
                case "src":
                    element.src = button_attrb[1].encode()
                case "loop":
                    element.loop = eval(button_attrb[1])
                case "volume":
                    element.volume = float(button_attrb[1])
                case "autoplay":
                    element.autoplay = eval(button_attrb[1])
        
        if element.autoplay:
            element.play()
    
    def parseGraphicsEffect(self,widget:ET.Element):
        effect = None
        for effect_attrb in widget.items():
            match effect_attrb[0]:
                case "id":
                    self.WIDGET_REGISTRY[effect_attrb[1]] = effect
                    effect.setObjectName(effect_attrb[1])
                case "type":
                    match effect_attrb[1]:
                        case "blur":
                            effect = QGraphicsBlurEffect()
                        case "opacity":
                            effect = QGraphicsOpacityEffect()
                        case "shadow":
                            effect = QGraphicsDropShadowEffect()
                        case "color":
                            effect = QGraphicsColorizeEffect()
                        case "glow":
                            effect = QGraphicsGlowEffect()
                case "enabled":
                    effect.setEnabled(bool(effect_attrb[1]))
                case "radius":
                    if hasattr(effect,"blurRadius"):
                        effect.setBlurRadius(float(effect_attrb[1]))
                case "blur-hints":
                    hints = None
                    if effect_attrb[1].find("|") != -1:
                        hints = effect_attrb[1].split("|")
                        if len(hints) == 1:
                            hints = self.getBlurHintsByName(hints[0])
                        elif len(hints) == 2:
                            hints = self.getBlurHintsByName(hints[0]) | self.getBlurHintsByName(hints[1])
                        else:
                            hints = self.getBlurHintsByName(hints[0]) | self.getBlurHintsByName(hints[1]) | self.getBlurHintsByName(hints[2])

                    else:
                        hints = self.getBlurHintsByName(effect_attrb[1])
                    effect.setBlurHints(hints)
                case "opacity":
                    if hasattr(effect,"opacity"):
                        effect.setOpacity(float(effect_attrb[1]))
                case "mask":
                    if hasattr(effect,"opacityMask"):
                        effect.setOpacityMask(QColor(effect_attrb[1]))
                case "color":
                    if hasattr(effect,"color"):
                        effect.setColor(QColor(effect_attrb[1]))
                case "strength":
                    if hasattr(effect,"strength"):
                        effect.setStrength(float(effect_attrb[1]))
                case "offset":
                    if hasattr(effect,"offset"):
                        effect.setOffset(*[float(eff) for eff in effect_attrb[1].split(" ")])
                case "distance":
                    if hasattr(effect,"distance"):
                        effect.setDistance(float(effect_attrb[1]))

    def parseAnimation(self,widget:ET.Element):
        animation = None
        for anim_attrb in widget.items():
            match anim_attrb[0]:
                case "id":
                    self.WIDGET_REGISTRY[anim_attrb[1]] = animation
                    animation.setObjectName(anim_attrb[1])
                case "type":
                    match anim_attrb[1]:
                        case "property":
                            animation = QPropertyAnimation()
                        case "variant":
                            animation = QVariantAnimation()
                case "duration":
                    animation.setDuration(int(anim_attrb[1]))
                case "count":
                    animation.setLoopCount(int(anim_attrb[1]))
                case "start":
                    if eval(anim_attrb[1]) == True:
                        animation.start()
                case "start-value":
                    animation.setStartValue(eval(anim_attrb[1]))
                case "end-value":
                    animation.setEndValue(eval(anim_attrb[1]))
                case "easing-curve":
                    animation.setEasingCurve(self.getEasingCurveByName(anim_attrb[1]))
                case "property":
                    if hasattr(animation,"property"):
                        animation.setPropertyName(anim_attrb[1].encode("utf-8"))
                case "onFinish":
                    animation.finished.connect(functools.partial(self.bindDynamicEvent,anim_attrb[1]))
                case "onValueChange":
                    animation.valueChanged.connect(functools.partial(self.bindDynamicEvent,anim_attrb[1]))
                case "onLoopChange":
                    animation.currentLoopChanged.connect(functools.partial(self.bindDynamicEvent,anim_attrb[1]))
                case "onDirectionChange":
                    animation.directionChanged.connect(functools.partial(self.bindDynamicEvent,anim_attrb[1]))
                case "onStateChange":
                    animation.stateChanged.connect(functools.partial(self.bindDynamicEvent,anim_attrb[1]))

    def parseTimer(self,widget:ET.Element):
        timer = QTimer()
        for timer_attrb in widget.items():
            match timer_attrb[0]:
                case "id":
                    self.WIDGET_REGISTRY[timer_attrb[1]] = timer
                    timer.setObjectName(timer_attrb[1])
                case "interval":
                    timer.setInterval(int(timer_attrb[1]))
                case "single-shot":
                    timer.setSingleShot(eval(timer_attrb[1]))
                case "start":
                    if eval(timer_attrb[1]) == True:
                        timer.start()
                case "onTimeOut":
                    timer.timeout.connect(functools.partial(self.bindDynamicEvent,timer_attrb[1]))

    def parseFontLoader(self,widget:ET.Element):
        for font_attrb in widget.items():
            match font_attrb[0]:
                case "src":
                    if font_attrb[1][:4] == "res:":
                        QFontDatabase.addApplicationFontFromData(self.RESOURCE[font_attrb[1][6:]])
                        del Engine.RESOURCE[font_attrb[1][6:]]
                    else:
                        QFontDatabase.addApplicationFont(self.RESOURCE[font_attrb[1]])
                        del Engine.RESOURCE[font_attrb[1]]

    #Load Resource By Name
    def loadResourceByName(self,res:str) -> QPixmap:
        if res[:4] == "res:":
           pixmap = QPixmap()
           pixmap.loadFromData(self.RESOURCE[res[6:]])
           return pixmap
        else:
            return QPixmap(res)

    # Get Window Type By Name
    def getWindowTypeByName(self, type):
        match type:
            case 'BypassGraphicsProxyWidget':
                return Qt.WindowType.BypassGraphicsProxyWidget
            case 'BypassWindowManagerHint':
                return Qt.WindowType.BypassWindowManagerHint
            case 'CoverWindow':
                return Qt.WindowType.CoverWindow
            case 'CustomizeWindowHint':
                return Qt.WindowType.CustomizeWindowHint
            case 'Desktop':
                return Qt.WindowType.Desktop
            case 'Dialog':
                return Qt.WindowType.Dialog
            case 'Drawer':
                return Qt.WindowType.Drawer
            case 'ForeignWindow':
                return Qt.WindowType.ForeignWindow
            case 'FramelessWindowHint':
                return Qt.WindowType.FramelessWindowHint
            case 'MacWindowToolBarButtonHint':
                return Qt.WindowType.MacWindowToolBarButtonHint
            case 'MaximizeUsingFullscreenGeometryHint':
                return Qt.WindowType.MaximizeUsingFullscreenGeometryHint
            case 'MSWindowsFixedSizeDialogHint':
                return Qt.WindowType.MSWindowsFixedSizeDialogHint
            case 'MSWindowsOwnDC':
                return Qt.WindowType.MSWindowsOwnDC
            case 'NoDropShadowWindowHint':
                return Qt.WindowType.NoDropShadowWindowHint
            case 'Popup':
                return Qt.WindowType.Popup
            case 'Sheet':
                return Qt.WindowType.Sheet
            case 'SplashScreen':
                return Qt.WindowType.SplashScreen
            case 'SubWindow':
                return Qt.WindowType.SubWindow
            case 'Tool':
                return Qt.WindowType.Tool
            case 'ToolTip':
                return Qt.WindowType.ToolTip
            case 'Widget':
                return Qt.WindowType.Widget
            case 'Window':
                return Qt.WindowType.Window
            case 'WindowCloseButtonHint':
                return Qt.WindowType.WindowCloseButtonHint
            case 'WindowContextHelpButtonHint':
                return Qt.WindowType.WindowContextHelpButtonHint
            case 'WindowDoesNotAcceptFocus':
                return Qt.WindowType.WindowDoesNotAcceptFocus
            case 'WindowFullscreenButtonHint':
                return Qt.WindowType.WindowFullscreenButtonHint
            case 'WindowMaximizeButtonHint':
                return Qt.WindowType.WindowMaximizeButtonHint
            case 'WindowMinMaxButtonsHint':
                return Qt.WindowType.WindowMinMaxButtonsHint
            case 'WindowOverridesSystemGestures':
                return Qt.WindowType.WindowOverridesSystemGestures
            case 'WindowShadeButtonHint':
                return Qt.WindowType.WindowShadeButtonHint
            case 'WindowStaysOnBottomHint':
                return Qt.WindowType.WindowStaysOnBottomHint
            case 'WindowStaysOnTopHint':
                return Qt.WindowType.WindowStaysOnTopHint
            case 'WindowSystemMenuHint':
                return Qt.WindowType.WindowSystemMenuHint
            case 'WindowTitleHint':
                return Qt.WindowType.WindowTitleHint
            case 'WindowTransparentForInput':
                return Qt.WindowType.WindowTransparentForInput
            case 'WindowType_Mask':
                return Qt.WindowType.WindowType_Mask
            case 'X11BypassWindowManagerHint':
                return Qt.WindowType.X11BypassWindowManagerHint
    
    #Get Widget Attribute By Name
    def getWidgetAttributeByName(self, widAttr):
        match widAttr:
            case 'WA_AcceptDrops':
                return Qt.WidgetAttribute.WA_AcceptDrops
            case 'WA_AlwaysShowToolTips':
                return Qt.WidgetAttribute.WA_AlwaysShowToolTips
            case 'WA_AcceptTouchEvents':
                return Qt.WidgetAttribute.WA_AcceptTouchEvents
            case 'WA_AlwaysStackOnTop':
                return Qt.WidgetAttribute.WA_AlwaysStackOnTop
            case 'WA_AttributeCount':
                return Qt.WidgetAttribute.WA_AttributeCount
            case 'WA_ContentsMarginsRespectsSafeArea':
                return Qt.WidgetAttribute.WA_ContentsMarginsRespectsSafeArea
            case 'WA_CustomWhatsThis':
                return Qt.WidgetAttribute.WA_CustomWhatsThis
            case 'WA_DeleteOnClose':
                return Qt.WidgetAttribute.WA_DeleteOnClose
            case 'WA_Disabled':
                return Qt.WidgetAttribute.WA_Disabled
            case 'WA_DontCreateNativeAncestors':
                return Qt.WidgetAttribute.WA_DontCreateNativeAncestors
            case 'WA_DontShowOnScreen':
                return Qt.WidgetAttribute.WA_DontShowOnScreen
            case 'WA_ForceDisabled':
                return Qt.WidgetAttribute.WA_ForceDisabled
            case 'WA_ForceUpdatesDisabled':
                return Qt.WidgetAttribute.WA_ForceUpdatesDisabled
            case 'WA_GrabbedShortcut':
                return Qt.WidgetAttribute.WA_GrabbedShortcut
            case 'WA_GroupLeader':
                return Qt.WidgetAttribute.WA_GroupLeader
            case 'WA_Hover':
                return Qt.WidgetAttribute.WA_Hover
            case 'WA_InputMethodEnabled':
                return Qt.WidgetAttribute.WA_InputMethodEnabled
            case 'WA_InputMethodTransparent':
                return Qt.WidgetAttribute.WA_InputMethodTransparent
            case 'WA_InvalidSize':
                return Qt.WidgetAttribute.WA_InvalidSize
            case 'WA_KeyboardFocusChange':
                return Qt.WidgetAttribute.WA_KeyboardFocusChange
            case 'WA_KeyCompression':
                return Qt.WidgetAttribute.WA_KeyCompression
            case 'WA_LaidOut':
                return Qt.WidgetAttribute.WA_LaidOut
            case 'WA_LayoutOnEntireRect':
                return Qt.WidgetAttribute.WA_LayoutOnEntireRect
            case 'WA_LayoutUsesWidgetRect':
                return Qt.WidgetAttribute.WA_LayoutUsesWidgetRect
            case 'WA_MacAlwaysShowToolWindow':
                return Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow
            case 'WA_MacBrushedMetal':
                return Qt.WidgetAttribute.WA_MacBrushedMetal
            case 'WA_MacFrameworkScaled':
                return Qt.WidgetAttribute.WA_MacFrameworkScaled
            case 'WA_MacMetalStyle':
                return Qt.WidgetAttribute.WA_MacMetalStyle
            case 'WA_MacMiniSize':
                return Qt.WidgetAttribute.WA_MacMiniSize
            case 'WA_MacNoClickThrough':
                return Qt.WidgetAttribute.WA_MacNoClickThrough
            case 'WA_MacNormalSize':
                return Qt.WidgetAttribute.WA_MacNormalSize
            case 'WA_MacNoShadow':
                return Qt.WidgetAttribute.WA_MacNoShadow
            case 'WA_MacOpaqueSizeGrip':
                return Qt.WidgetAttribute.WA_MacOpaqueSizeGrip
            case 'WA_MacShowFocusRect':
                return Qt.WidgetAttribute.WA_MacShowFocusRect
            case 'WA_MacSmallSize':
                return Qt.WidgetAttribute.WA_MacSmallSize
            case 'WA_MacVariableSize':
                return Qt.WidgetAttribute.WA_MacVariableSize
            case 'WA_Mapped':
                return Qt.WidgetAttribute.WA_Mapped
            case 'WA_MouseNoMask':
                return Qt.WidgetAttribute.WA_MouseNoMask
            case 'WA_MouseTracking':
                return Qt.WidgetAttribute.WA_MouseTracking
            case 'WA_Moved':
                return Qt.WidgetAttribute.WA_Moved
            case 'WA_MSWindowsUseDirect3D':
                return Qt.WidgetAttribute.WA_MSWindowsUseDirect3D
            case 'WA_NativeWindow':
                return Qt.WidgetAttribute.WA_NativeWindow
            case 'WA_NoChildEventsForParent':
                return Qt.WidgetAttribute.WA_NoChildEventsForParent
            case 'WA_NoChildEventsFromChildren':
                return Qt.WidgetAttribute.WA_NoChildEventsFromChildren
            case 'WA_NoMousePropagation':
                return Qt.WidgetAttribute.WA_NoMousePropagation
            case 'WA_NoMouseReplay':
                return Qt.WidgetAttribute.WA_NoMouseReplay
            case 'WA_NoSystemBackground':
                return Qt.WidgetAttribute.WA_NoSystemBackground
            case 'WA_NoX11EventCompression':
                return Qt.WidgetAttribute.WA_NoX11EventCompression
            case 'WA_OpaquePaintEvent':
                return Qt.WidgetAttribute.WA_OpaquePaintEvent
            case 'WA_OutsideWSRange':
                return Qt.WidgetAttribute.WA_OutsideWSRange
            case 'WA_PaintOnScreen':
                return Qt.WidgetAttribute.WA_PaintOnScreen
            case 'WA_PaintUnclipped':
                return Qt.WidgetAttribute.WA_PaintUnclipped
            case 'WA_PendingMoveEvent':
                return Qt.WidgetAttribute.WA_PendingMoveEvent
            case 'WA_PendingResizeEvent':
                return Qt.WidgetAttribute.WA_PendingResizeEvent
            case 'WA_PendingUpdate':
                return Qt.WidgetAttribute.WA_PendingUpdate
            case 'WA_QuitOnClose':
                return Qt.WidgetAttribute.WA_QuitOnClose
            case 'WA_Resized':
                return Qt.WidgetAttribute.WA_Resized
            case 'WA_RightToLeft':
                return Qt.WidgetAttribute.WA_RightToLeft
            case 'WA_SetCursor':
                return Qt.WidgetAttribute.WA_SetCursor
            case 'WA_SetFont':
                return Qt.WidgetAttribute.WA_SetFont
            case 'WA_SetLayoutDirection':
                return Qt.WidgetAttribute.WA_SetLayoutDirection
            case 'WA_SetLocale':
                return Qt.WidgetAttribute.WA_SetLocale
            case 'WA_SetPalette':
                return Qt.WidgetAttribute.WA_SetPalette
            case 'WA_SetStyle':
                return Qt.WidgetAttribute.WA_SetStyle
            case 'WA_SetWindowIcon':
                return Qt.WidgetAttribute.WA_SetWindowIcon
            case 'WA_ShowWithoutActivating':
                return Qt.WidgetAttribute.WA_ShowWithoutActivating
            case 'WA_StaticContents':
                return Qt.WidgetAttribute.WA_StaticContents
            case 'WA_StyledBackground':
                return Qt.WidgetAttribute.WA_StyledBackground
            case 'WA_StyleSheet':
                return Qt.WidgetAttribute.WA_StyleSheet
            case 'WA_StyleSheetTarget':
                return Qt.WidgetAttribute.WA_StyleSheetTarget
            case 'WA_TabletTracking':
                return Qt.WidgetAttribute.WA_TabletTracking
            case 'WA_TintedBackground':
                return Qt.WidgetAttribute.WA_TintedBackground
            case 'WA_TouchPadAcceptSingleTouchEvents':
                return Qt.WidgetAttribute.WA_TouchPadAcceptSingleTouchEvents
            case 'WA_TranslucentBackground':
                return Qt.WidgetAttribute.WA_TranslucentBackground
            case 'WA_TransparentForMouseEvents':
                return Qt.WidgetAttribute.WA_TransparentForMouseEvents
            case 'WA_UnderMouse':
                return Qt.WidgetAttribute.WA_UnderMouse
            case 'WA_UpdatesDisabled':
                return Qt.WidgetAttribute.WA_UpdatesDisabled
            case 'WA_WindowModified':
                return Qt.WidgetAttribute.WA_WindowModified
            case 'WA_WindowPropagation':
                return Qt.WidgetAttribute.WA_WindowPropagation
            case 'WA_WState_CompressKeys':
                return Qt.WidgetAttribute.WA_WState_CompressKeys
            case 'WA_WState_ExplicitShowHide':
                return Qt.WidgetAttribute.WA_WState_ExplicitShowHide
            case 'WA_WState_ConfigPending':
                return Qt.WidgetAttribute.WA_WState_ConfigPending
            case 'WA_WState_Created':
                return Qt.WidgetAttribute.WA_WState_Created
            case 'WA_WState_Hidden':
                return Qt.WidgetAttribute.WA_WState_Hidden
            case 'WA_WState_InPaintEvent':
                return Qt.WidgetAttribute.WA_WState_InPaintEvent
            case 'WA_WState_Reparented':
                return Qt.WidgetAttribute.WA_WState_Reparented
            case 'WA_WState_OwnSizePolicy':
                return Qt.WidgetAttribute.WA_WState_OwnSizePolicy
            case 'WA_WState_Polished':
                return Qt.WidgetAttribute.WA_WState_Polished
            case 'WA_WState_Visible':
                return Qt.WidgetAttribute.WA_WState_Visible
            case 'WA_X11DoNotAcceptFocus':
                return Qt.WidgetAttribute.WA_X11DoNotAcceptFocus
            case 'WA_X11NetWmWindowTypeCombo':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeCombo
            case 'WA_X11NetWmWindowTypeDesktop':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeDesktop
            case 'WA_X11NetWmWindowTypeDialog':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeDialog
            case 'WA_X11NetWmWindowTypeDND':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeDND
            case 'WA_X11NetWmWindowTypeDock':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeDock
            case 'WA_X11NetWmWindowTypeDropDownMenu':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeDropDownMenu
            case 'WA_X11NetWmWindowTypeMenu':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeMenu
            case 'WA_X11NetWmWindowTypeNotification':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeNotification
            case 'WA_X11NetWmWindowTypePopupMenu':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypePopupMenu
            case 'WA_X11NetWmWindowTypeSplash':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeSplash
            case 'WA_X11NetWmWindowTypeToolBar':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeToolBar
            case 'WA_X11NetWmWindowTypeToolTip':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeToolTip
            case 'WA_X11NetWmWindowTypeUtility':
                return Qt.WidgetAttribute.WA_X11NetWmWindowTypeUtility
            case 'WA_X11OpenGLOverlay':
                return Qt.WidgetAttribute.WA_X11OpenGLOverlay

    #Get Text Format By Name
    def getTextFormatByName(self,format):
        match format:
            case "PlainText":
                return Qt.TextFormat.PlainText
            case "RichText":
                return Qt.TextFormat.RichText
            case "AutoText":
                return Qt.TextFormat.AutoText
            case "MarkdownText":
                return Qt.TextFormat.MarkdownText

    #Get Alignment By UI String Property
    def getAlignmentByName(self,anchor):
        match anchor:
            case "left":
                return Qt.AlignmentFlag.AlignLeft
            case "right":
                return Qt.AlignmentFlag.AlignRight
            case "top":
                return Qt.AlignmentFlag.AlignTop
            case "bottom":
                return Qt.AlignmentFlag.AlignBottom
            case "center":
                return Qt.AlignmentFlag.AlignCenter
            case "absolute":
                return Qt.AlignmentFlag.AlignAbsolute
            case "justify":
                return Qt.AlignmentFlag.AlignJustify
            case "hcenter":
                return Qt.AlignmentFlag.AlignHCenter
            case "vcenter":
                return Qt.AlignmentFlag.AlignVCenter
            case "baseline":
                return Qt.AlignmentFlag.AlignBaseline
            case "trailing":
                return Qt.AlignmentFlag.AlignTrailing
            case "leading":
                return Qt.AlignmentFlag.AlignLeading
            case "horizontal_mask":
                return Qt.AlignmentFlag.AlignHorizontal_Mask
            case "vertical_mask":
                return Qt.AlignmentFlag.AlignVertical_Mask
    
    # Get Text In teraction Flag By Name
    def getTextInteractionFlagByName(self, flag):
        match flag:
            case 'LinksAccessibleByKeyboard':
                return Qt.TextInteractionFlag.LinksAccessibleByKeyboard
            case 'LinksAccessibleByMouse':
                return Qt.TextInteractionFlag.LinksAccessibleByMouse
            case 'NoTextInteraction':
                return Qt.TextInteractionFlag.NoTextInteraction
            case 'TextBrowserInteraction':
                return Qt.TextInteractionFlag.TextBrowserInteraction
            case 'TextEditable':
                return Qt.TextInteractionFlag.TextEditable
            case 'TextEditorInteraction':
                return Qt.TextInteractionFlag.TextEditorInteraction
            case 'TextSelectableByKeyboard':
                return Qt.TextInteractionFlag.TextSelectableByKeyboard
            case 'TextSelectableByMouse':
                return Qt.TextInteractionFlag.TextSelectableByMouse

    #Get CheckState By Name
    def getCheckStateByName(self,state):
        match state:
            case "unchecked":
                return Qt.CheckState.Unchecked
            case "checked":
                return Qt.CheckState.Checked
            case "partial":
                return Qt.CheckState.PartiallyChecked

    #Get Tick Position By Name
    def getTickPositionByName(self,pos):
        match pos:
            case "NoTicks":
                return QSlider.TickPosition.NoTicks
            case "TicksAbove":
                return QSlider.TickPosition.TicksAbove
            case "TicksBelow":
                return QSlider.TickPosition.TicksBelow
            case "TicksBothSides":
                return QSlider.TickPosition.TicksBothSides
            case "TicksLeft":
                return QSlider.TickPosition.TicksLeft
            case "TicksRight":
                return QSlider.TickPosition.TicksRight

    #Get StepType By Name
    def getStepTypeByName(self,stype):
        match stype:
            case "default":
                return QAbstractSpinBox.StepType.DefaultStepType
            case "adaptive":
                return QAbstractSpinBox.StepType.AdaptiveDecimalStepType
   
    #Get LCD Mode By Name
    def getLCDModeByName(self,mode):
        match mode:
            case "dec":
                return QLCDNumber.Mode.Dec
            case "oct":
                return QLCDNumber.Mode.Oct
            case "bin":
                return QLCDNumber.Mode.Bin
            case "hex":
                return QLCDNumber.Mode.Hex
    
    #Get LCD Segment By Name
    def getLCDSegmentByName(self,segment):
        match segment:
            case "filled":
                return QLCDNumber.SegmentStyle.Filled
            case "flat":
                return QLCDNumber.SegmentStyle.Flat
            case "outline":
                return QLCDNumber.SegmentStyle.Outline
    
    #Get Echo Mode By Name
    def getEchoModeByName(self,mode):
        match mode:
            case "no-echo":
                return QLineEdit.EchoMode.NoEcho
            case "normal":
                return QLineEdit.EchoMode.Normal
            case "password":
                return QLineEdit.EchoMode.Password
            case "password-echo-on-edit":
                return QLineEdit.EchoMode.PasswordEchoOnEdit

    #Get Elide Mode By Name
    def getElideModeByName(self,mode):
        match mode:
            case "left":
                return Qt.TextElideMode.ElideLeft
            case "right":
                return Qt.TextElideMode.ElideRight
            case "none":
                return Qt.TextElideMode.ElideNone
            case "middle":
                return Qt.TextElideMode.ElideMiddle

    #Get Selection Behaviour By Name
    def getSelectionBehaviourByName(self,behav):
        match behav:
            case "left-tab":
                return QTabBar.SelectionBehavior.SelectLeftTab
            case "right-tab":
                return QTabBar.SelectionBehavior.SelectRightTab
            case "prev-tab":
                return QTabBar.SelectionBehavior.SelectPreviousTab

    #Get Tab Bar Shape By Name
    def getTabBarShapeByName(self,shape):
        match shape:
            case "rounded-east":
                return QTabBar.Shape.RoundedEast
            case "rounded-west":
                return QTabBar.Shape.RoundedWest
            case "rounded-north":
                return QTabBar.Shape.RoundedNorth
            case "rounded-south":
                return QTabBar.Shape.RoundedSouth
            case "triangular-east":
                return QTabBar.Shape.TriangularEast
            case "triangular-west":
                return QTabBar.Shape.TriangularWest
            case "triangular-north":
                return QTabBar.Shape.TriangularNorth
            case "triangular-south":
                return QTabBar.Shape.TriangularSouth

    #Get Tab Position By Name
    def getTabPositionByName(self,pos):
        match pos:
            case "east":
                return QTabWidget.TabPosition.East
            case "west":
                return QTabWidget.TabPosition.West
            case "north":
                return QTabWidget.TabPosition.North
            case "south":
                return QTabWidget.TabPosition.South

    #Get Blur Hints By Name
    def getBlurHintsByName(self,hint):
        match hint:
            case "performance":
                return QGraphicsBlurEffect.BlurHint.PerformanceHint
            case "quality":
                return QGraphicsBlurEffect.BlurHint.QualityHint
            case "animation":
                return QGraphicsBlurEffect.BlurHint.AnimationHint

    #Get Easing Curve By Name
    def getEasingCurveByName(self,curve):
        # Normalize the input (lowercase, strip whitespace, replace underscores/hyphens)
        curve = curve.strip().lower().replace("_", "").replace("-", "")
        
        match curve:
            # Linear
            case "linear":
                return QEasingCurve.Type.Linear
                
            # Quadratic
            case "inquad" | "inquadratic":
                return QEasingCurve.Type.InQuad
            case "outquad" | "outquadratic":
                return QEasingCurve.Type.OutQuad
            case "inoutquad" | "inoutquadratic":
                return QEasingCurve.Type.InOutQuad
            case "outinquad" | "outinquadratic":
                return QEasingCurve.Type.OutInQuad
                
            # Cubic
            case "incubic" | "incube":
                return QEasingCurve.Type.InCubic
            case "outcubic" | "outcube":
                return QEasingCurve.Type.OutCubic
            case "inoutcubic" | "inoutcube":
                return QEasingCurve.Type.InOutCubic
            case "outincubic" | "outincube":
                return QEasingCurve.Type.OutInCubic
                
            # Quartic
            case "inquart" | "inquartic":
                return QEasingCurve.Type.InQuart
            case "outquart" | "outquartic":
                return QEasingCurve.Type.OutQuart
            case "inoutquart" | "inoutquartic":
                return QEasingCurve.Type.InOutQuart
            case "outinquart" | "outinquartic":
                return QEasingCurve.Type.OutInQuart
                
            # Quintic
            case "inquint" | "inquintic":
                return QEasingCurve.Type.InQuint
            case "outquint" | "outquintic":
                return QEasingCurve.Type.OutQuint
            case "inoutquint" | "inoutquintic":
                return QEasingCurve.Type.InOutQuint
            case "outinquint" | "outinquintic":
                return QEasingCurve.Type.OutInQuint
                
            # Sinusoidal
            case "insine" | "insinusoidal":
                return QEasingCurve.Type.InSine
            case "outsine" | "outsinusoidal":
                return QEasingCurve.Type.OutSine
            case "inoutsine" | "inoutsinusoidal":
                return QEasingCurve.Type.InOutSine
            case "outinsine" | "outinsinusoidal":
                return QEasingCurve.Type.OutInSine
                
            # Exponential
            case "inexpo" | "inexponential":
                return QEasingCurve.Type.InExpo
            case "outexpo" | "outexponential":
                return QEasingCurve.Type.OutExpo
            case "inoutexpo" | "inoutexponential":
                return QEasingCurve.Type.InOutExpo
            case "outinexpo" | "outinexponential":
                return QEasingCurve.Type.OutInExpo
                
            # Circular
            case "incirc" | "incircular":
                return QEasingCurve.Type.InCirc
            case "outcirc" | "outcircular":
                return QEasingCurve.Type.OutCirc
            case "inoutcirc" | "inoutcircular":
                return QEasingCurve.Type.InOutCirc
            case "outincirc" | "outincircular":
                return QEasingCurve.Type.OutInCirc
                
            # Elastic
            case "inelastic":
                return QEasingCurve.Type.InElastic
            case "outelastic":
                return QEasingCurve.Type.OutElastic
            case "inoutelastic":
                return QEasingCurve.Type.InOutElastic
            case "outinelastic":
                return QEasingCurve.Type.OutInElastic
                
            # Back
            case "inback":
                return QEasingCurve.Type.InBack
            case "outback":
                return QEasingCurve.Type.OutBack
            case "inoutback":
                return QEasingCurve.Type.InOutBack
            case "outinback":
                return QEasingCurve.Type.OutInBack
                
            # Bounce
            case "inbounce":
                return QEasingCurve.Type.InBounce
            case "outbounce":
                return QEasingCurve.Type.OutBounce
            case "inoutbounce":
                return QEasingCurve.Type.InOutBounce
            case "outinbounce":
                return QEasingCurve.Type.OutInBounce
                
            # Special curves
            case "incurve":
                return QEasingCurve.Type.InCurve
            case "outcurve":
                return QEasingCurve.Type.OutCurve
            case "sinecurve":
                return QEasingCurve.Type.SineCurve
            case "cosinecurve":
                return QEasingCurve.Type.CosineCurve
            case "bezierspline":
                return QEasingCurve.Type.BezierSpline
            case "tcbspline":
                return QEasingCurve.Type.TCBSpline
            case "custom":
                return QEasingCurve.Type.Custom
                
            case _:
                raise ValueError(f"Unknown easing curve: '{curve}'. ")

    #Get Scroll Bar Policy By Name
    def getScrollBarPolicyByName(self,policy):
        match policy:
            case "ScrollBarAsNeeded":
                return Qt.ScrollBarPolicy.ScrollBarAsNeeded
            case "ScrollBarAlwaysOn":
                return Qt.ScrollBarPolicy.ScrollBarAlwaysOn
            case "ScrollBarAlwaysOff":
                return Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    #Get Word Wrap Mode By Name
    def getWordWrapModeByName(self,mode):
        match mode:
            case "ManualWrap":
                return QTextOption.WrapMode.ManualWrap
            case "WordWrap":
                return QTextOption.WrapMode.WordWrap
            case "WrapAnywhere":
                return QTextOption.WrapMode.WrapAnywhere
            case "WrapAtWordBoundaryOrAnywhere":
                return QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
            case "NoWrap":
                return QTextOption.WrapMode.NoWrap
    
    #Get Line Wrap Mode By Name
    def getLineWrapModeByName(self,mode):
        match mode:
            case "FixedColumnWidth":
                return QTextEdit.LineWrapMode.FixedColumnWidth
            case "FixedPixelWidth":
                return QTextEdit.LineWrapMode.FixedPixelWidth
            case "NoWrap":
                return QTextEdit.LineWrapMode.NoWrap
    
    #Get Size Policy By Name
    def getSizePolicyByName(self,policy):
        match policy:
            case "Expanding":
                return QSizePolicy.Policy.Expanding
            case "Fixed":
                return QSizePolicy.Policy.Fixed
            case "Ignored":
                return QSizePolicy.Policy.Ignored
            case "Maximum":
                return QSizePolicy.Policy.Maximum
            case "Minimum":
                return QSizePolicy.Policy.Minimum
            case "MinimumExpanding":
                return QSizePolicy.Policy.MinimumExpanding
            case "Preferred":
                return QSizePolicy.Policy.Preferred

    #Get Cursor Shape By Name
    def getCursorShapeByName(self,shape: str) -> Qt.CursorShape:
        match shape:
            case "ArrowCursor":
                return Qt.ArrowCursor
            case "UpArrowCursor":
                return Qt.UpArrowCursor
            case "CrossCursor":
                return Qt.CrossCursor
            case "WaitCursor":
                return Qt.WaitCursor
            case "IBeamCursor":
                return Qt.IBeamCursor
            case "SizeVerCursor":
                return Qt.SizeVerCursor
            case "SizeHorCursor":
                return Qt.SizeHorCursor
            case "SizeBDiagCursor":
                return Qt.SizeBDiagCursor
            case "SizeFDiagCursor":
                return Qt.SizeFDiagCursor
            case "SizeAllCursor":
                return Qt.SizeAllCursor
            case "BlankCursor":
                return Qt.BlankCursor
            case "SplitVCursor":
                return Qt.SplitVCursor
            case "SplitHCursor":
                return Qt.SplitHCursor
            case "PointingHandCursor":
                return Qt.PointingHandCursor
            case "ForbiddenCursor":
                return Qt.ForbiddenCursor
            case "WhatsThisCursor":
                return Qt.WhatsThisCursor
            case "BusyCursor":
                return Qt.BusyCursor if hasattr(Qt, "BusyCursor") else Qt.WaitCursor
            case "OpenHandCursor":
                return Qt.OpenHandCursor
            case "ClosedHandCursor":
                return Qt.ClosedHandCursor
            case "DragCopyCursor":
                return Qt.DragCopyCursor
            case "DragMoveCursor":
                return Qt.DragMoveCursor
            case "DragLinkCursor":
                return Qt.DragLinkCursor
            case _:
                return Qt.ArrowCursor  # default fallback

    #Get Access To Engine Functions
    def getEngineFunctionByName(self,name):
        return globals().get(name)

    #Get Widget Element By ID
    def getElementByID(self,ID:str) -> object:
        return self.WIDGET_REGISTRY.get(ID)
    
    #Delete Widget Elemebt By ID
    def deleteElementByID(self,ID:str):
        element:QWidget =  self.WIDGET_REGISTRY.get(ID)
        if element:
            if hasattr(element,"deleteLater"):
                element.deleteLater()
            del self.WIDGET_REGISTRY[ID]
        del element

    #Load Engine Resource 
    def loadEngineResource(self,res:str):
        Engine.RESOURCE = Resource.loadResource(res)

if __name__ == "__main__":
    app = QApplication([])
    engine = Engine((800,600))
    t = time.time()
    window = engine.load("launcher.xml")
    print(time.time()-t)
    window.show()
    app.exec()
