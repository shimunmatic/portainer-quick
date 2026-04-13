from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import (
    QMessageBox, QPushButton, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QTabWidget,
    QScrollArea, QGroupBox, QComboBox, QSystemTrayIcon, QMenu,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, QObject, QRunnable, QThreadPool, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont
from enum import Enum
import sys
import json
from types import SimpleNamespace
import requests
from pathlib import Path
import urllib3

try:
    from PyQt6.QtSvg import QSvgRenderer
    _SVG_AVAILABLE = True
except ImportError:
    _SVG_AVAILABLE = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# --- Stylesheet ---

APP_STYLE = """
QWidget#MainWindow {
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid palette(mid);
    border-radius: 4px;
    padding: 4px;
}
QTabBar::tab {
    padding: 6px 20px;
    margin-right: 2px;
    border: 1px solid palette(mid);
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: palette(base);
    border-bottom: 2px solid #13bef9;
}

QScrollArea {
    border: none;
}
QGroupBox {
    border: none;
    margin-top: 0;
    padding-top: 0;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0;
}

QPushButton {
    padding: 5px 14px;
    border: 1px solid palette(mid);
    border-radius: 4px;
    font-size: 12px;
}
QPushButton:hover {
    border-color: #13bef9;
}
QPushButton:pressed {
    background: palette(midlight);
}
QPushButton:disabled {
    opacity: 0.5;
}

QPushButton#startBtn {
    background-color: #27ae60;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#startBtn:hover {
    background-color: #2ecc71;
}
QPushButton#startBtn:pressed {
    background-color: #1e8449;
}
QPushButton#startBtn:disabled {
    background-color: #7dcea0;
}

QPushButton#stopBtn {
    background-color: #c0392b;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#stopBtn:hover {
    background-color: #e74c3c;
}
QPushButton#stopBtn:pressed {
    background-color: #922b21;
}
QPushButton#stopBtn:disabled {
    background-color: #d98880;
}

QPushButton#dangerBtn {
    background-color: #c0392b;
    color: white;
    border: none;
}
QPushButton#dangerBtn:hover {
    background-color: #e74c3c;
}

QPushButton#accentBtn {
    background-color: #13bef9;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#accentBtn:hover {
    background-color: #45cbfa;
}
QPushButton#accentBtn:pressed {
    background-color: #0e9fd4;
}

QPushButton#favBtn {
    border: none;
    background: transparent;
    font-size: 16px;
    padding: 2px 4px;
    min-width: 24px;
    max-width: 24px;
}
QPushButton#favBtn:hover {
    background: palette(midlight);
    border-radius: 12px;
}

QLabel#statusDot {
    border-radius: 5px;
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
}
QLabel#statusDotActive {
    background-color: #27ae60;
    border-radius: 5px;
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
}
QLabel#statusDotInactive {
    background-color: #c0392b;
    border-radius: 5px;
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
}

QLabel#instanceLabel {
    color: palette(dark);
    font-size: 11px;
}

QLabel#sectionSeparator {
    color: palette(mid);
    font-size: 11px;
    padding: 4px 0 2px 4px;
}

QFrame#separator {
    background-color: palette(mid);
    max-height: 1px;
    margin: 4px 8px;
}

QWidget#itemCard {
    border: 1px solid palette(midlight);
    border-radius: 6px;
    padding: 2px;
    margin: 1px 0;
}
QWidget#itemCard:hover {
    border-color: #13bef9;
}

QListWidget {
    border: 1px solid palette(mid);
    border-radius: 4px;
    padding: 2px;
}
QListWidget::item {
    padding: 4px;
    border-radius: 2px;
}
QListWidget::item:selected {
    background-color: #13bef9;
    color: white;
}

QComboBox {
    padding: 4px 8px;
    border: 1px solid palette(mid);
    border-radius: 4px;
}

QLineEdit {
    padding: 6px 8px;
    border: 1px solid palette(mid);
    border-radius: 4px;
}
QLineEdit:focus {
    border-color: #13bef9;
}
"""


# --- Icon Helpers ---

def _resolve_svg_path():
    installed = Path.home() / '.local' / 'share' / 'portainer-quick' / 'portainer.svg'
    dev = Path(__file__).parent / 'resources' / 'portainer.svg'
    return installed if installed.exists() else dev


def _make_tray_icon(svg_path, all_ok):
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    if _SVG_AVAILABLE and svg_path.exists():
        renderer = QSvgRenderer(str(svg_path))
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

    dot_size = 14
    dot_x = size - dot_size - 2
    dot_y = size - dot_size - 2
    dot_color = QColor('#27ae60') if all_ok else QColor('#c0392b')
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(dot_color))
    painter.setPen(QColor(0, 0, 0, 0))
    painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)
    painter.end()

    return QIcon(pixmap)


def _clear_layout(layout):
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        widget = item.widget()
        if widget:
            widget.setParent(None)
        else:
            layout.removeItem(item)


# --- Config ---

CONFIG_FOLDER = Path.home() / '.config' / 'portainer-quick'
CONFIG_PATH = CONFIG_FOLDER / 'config.json'

DEFAULT_CONFIG = {
    "instances": [
        {
            "active": False,
            "name": "NAME",
            "url": "https://127.0.0.1:9443",
            "apiKey": "",
            "environmentId": 0
        }
    ],
    "groups": [],
    "favouriteStacks": [],
    "favouriteGroups": []
}


class AppConfig:

    def __init__(self, instances, groups, favourite_stacks, favourite_groups, raw):
        self.instances = instances
        self.groups = groups
        self.favourite_stacks = favourite_stacks
        self.favourite_groups = favourite_groups
        self._raw = raw

    @classmethod
    def load(cls):
        CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
        if not CONFIG_PATH.is_file():
            with open(CONFIG_PATH, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            print("Config file created at", CONFIG_PATH)
            sys.exit(1)

        with open(CONFIG_PATH) as f:
            raw = json.load(f)

        instances = json.loads(
            json.dumps(raw['instances']),
            object_hook=lambda d: SimpleNamespace(**d)
        )
        for instance in instances:
            instance.active = True
            if instance.apiKey == '' or instance.url == '' or instance.name == '' or instance.environmentId == 0:
                print(f"Instance '{getattr(instance, 'name', '?')}': apiKey, url, name, or environmentId not defined")
                sys.exit(1)

        groups = raw.get('groups', [])
        favourite_stacks = raw.get('favouriteStacks', [])
        favourite_groups = raw.get('favouriteGroups', [])
        return cls(instances, groups, favourite_stacks, favourite_groups, raw)

    def save(self):
        self._raw['groups'] = self.groups
        self._raw['favouriteStacks'] = self.favourite_stacks
        self._raw['favouriteGroups'] = self.favourite_groups
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self._raw, f, indent=4)

    def is_stack_favourite(self, stack_name, instance_name):
        return any(
            f['stackName'] == stack_name and f['instanceName'] == instance_name
            for f in self.favourite_stacks
        )

    def toggle_stack_favourite(self, stack_name, instance_name):
        if self.is_stack_favourite(stack_name, instance_name):
            self.favourite_stacks[:] = [
                f for f in self.favourite_stacks
                if not (f['stackName'] == stack_name and f['instanceName'] == instance_name)
            ]
        else:
            self.favourite_stacks.append({
                'stackName': stack_name,
                'instanceName': instance_name
            })
        self.save()

    def is_group_favourite(self, group_name):
        return group_name in self.favourite_groups

    def toggle_group_favourite(self, group_name):
        if self.is_group_favourite(group_name):
            self.favourite_groups.remove(group_name)
        else:
            self.favourite_groups.append(group_name)
        self.save()


# --- Data Model ---

class StackStatus(Enum):
    ACTIVE = 1
    INACTIVE = 2


class Stack:

    def __init__(self, name, status, id, instance):
        self.name = name
        self.id = id
        self.instance = instance
        self.status = StackStatus.ACTIVE if status == 1 else StackStatus.INACTIVE


# --- API Client ---

class PortainerClient:

    def __init__(self, instances):
        self.instances = instances

    def get_stacks(self):
        stacks = []
        for instance in self.instances:
            if instance.active:
                url = instance.url + '/api/stacks'
                headers = {
                    'Content-Type': 'application/json',
                    'X-API-Key': instance.apiKey
                }
                try:
                    response = requests.get(url, headers=headers, verify=False, timeout=10)
                    stack_list = response.json()
                    for stack in stack_list:
                        stacks.append(Stack(stack['Name'], stack['Status'], stack['Id'], instance))
                except requests.RequestException as e:
                    print(f"Error fetching stacks from {instance.name}: {e}")
        return stacks

    def _stack_action(self, stack, action):
        url = f'{stack.instance.url}/api/stacks/{stack.id}/{action}?endpointId={stack.instance.environmentId}'
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': stack.instance.apiKey
        }
        response = requests.post(url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        return response

    def start_stack(self, stack):
        return self._stack_action(stack, 'start')

    def stop_stack(self, stack):
        return self._stack_action(stack, 'stop')


# --- Async Workers ---

class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class AsyncWorker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.setAutoDelete(True)

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


# --- Spinner ---

SPINNER_FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]


class SpinnerButton(QPushButton):

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self._frame = 0
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)

    def start_spinning(self):
        self.setEnabled(False)
        self._frame = 0
        self._timer.start()

    def stop_spinning(self):
        self._timer.stop()
        self.setText(self._original_text)
        self.setEnabled(True)

    def _tick(self):
        self.setText(f"{SPINNER_FRAMES[self._frame]}  {self._original_text}...")
        self._frame = (self._frame + 1) % len(SPINNER_FRAMES)


# --- Stack Widgets ---

class StackItem(QtWidgets.QWidget):

    def __init__(self, stack, client, pool, config, reload_function):
        super().__init__()
        self.setObjectName("itemCard")
        self.stack = stack
        self._client = client
        self._pool = pool
        self._config = config
        self._reload = reload_function

        is_fav = config.is_stack_favourite(stack.name, stack.instance.name)
        self._fav_button = QPushButton("\u2605" if is_fav else "\u2606")
        self._fav_button.setObjectName("favBtn")
        self._fav_button.setToolTip("Toggle favourite")
        self._fav_button.clicked.connect(self._toggle_favourite)
        if is_fav:
            self._fav_button.setStyleSheet("QPushButton#favBtn { color: #f39c12; }")

        dot = QLabel()
        dot.setObjectName("statusDotActive" if stack.status is StackStatus.ACTIVE else "statusDotInactive")

        name_label = QLabel(f"<b>{stack.name}</b>")
        instance_label = QLabel(stack.instance.name)
        instance_label.setObjectName("instanceLabel")

        if stack.status is StackStatus.ACTIVE:
            self.button = SpinnerButton("Stop")
            self.button.setObjectName("stopBtn")
        else:
            self.button = SpinnerButton("Start")
            self.button.setObjectName("startBtn")
        self.button.clicked.connect(self._button_clicked)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        layout.addWidget(self._fav_button)
        layout.addWidget(dot)
        layout.addWidget(name_label)
        layout.addWidget(instance_label)
        layout.addStretch()
        layout.addWidget(self.button)
        self.setLayout(layout)
        self.setFixedHeight(self.sizeHint().height())

    def _toggle_favourite(self):
        self._config.toggle_stack_favourite(self.stack.name, self.stack.instance.name)
        is_fav = self._config.is_stack_favourite(self.stack.name, self.stack.instance.name)
        self._fav_button.setText("\u2605" if is_fav else "\u2606")
        if is_fav:
            self._fav_button.setStyleSheet("QPushButton#favBtn { color: #f39c12; }")
        else:
            self._fav_button.setStyleSheet("")

    def _button_clicked(self):
        self.button.start_spinning()
        reload_fn = self._reload

        if self.stack.status is StackStatus.ACTIVE:
            worker = AsyncWorker(self._client.stop_stack, self.stack)
        else:
            worker = AsyncWorker(self._client.start_stack, self.stack)

        worker.signals.finished.connect(lambda _: reload_fn())
        worker.signals.error.connect(lambda e: print(f"Stack action error: {e}"))
        self._pool.start(worker)


# --- Group Widgets ---

class GroupItem(QtWidgets.QWidget):

    def __init__(self, group, all_stacks, client, pool, reload_function, config):
        super().__init__()
        self.setObjectName("itemCard")
        self.group = group
        self._all_stacks = all_stacks
        self._client = client
        self._pool = pool
        self.reload_function = reload_function
        self._config = config
        self._batch_id = 0
        self._pending = 0

        self._resolved = self._resolve_stacks()
        active = self._is_active()
        members_count = len(group.get('stacks', []))
        active_count = sum(1 for s in self._resolved if s.status is StackStatus.ACTIVE)

        is_fav = config.is_group_favourite(group['name'])
        self._fav_button = QPushButton("\u2605" if is_fav else "\u2606")
        self._fav_button.setObjectName("favBtn")
        self._fav_button.setToolTip("Toggle favourite")
        self._fav_button.clicked.connect(self._toggle_favourite)
        if is_fav:
            self._fav_button.setStyleSheet("QPushButton#favBtn { color: #f39c12; }")

        dot = QLabel()
        if members_count == 0:
            dot.setObjectName("statusDotInactive")
        elif active:
            dot.setObjectName("statusDotActive")
        else:
            dot.setObjectName("statusDotInactive")

        name_label = QLabel(f"<b>{group['name']}</b>")
        status_label = QLabel(f"{active_count}/{members_count}")
        status_label.setObjectName("instanceLabel")

        self.start_button = SpinnerButton("Start All")
        self.start_button.setObjectName("startBtn")
        self.start_button.clicked.connect(self._start_all)

        self.stop_button = SpinnerButton("Stop All")
        self.stop_button.setObjectName("stopBtn")
        self.stop_button.clicked.connect(self._stop_all)

        self.manage_button = QPushButton("Manage")
        self.manage_button.clicked.connect(self._manage)

        if active:
            self.start_button.setEnabled(False)
        elif members_count == 0:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
        else:
            all_inactive = all(s.status is StackStatus.INACTIVE for s in self._resolved)
            if all_inactive:
                self.stop_button.setEnabled(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        layout.addWidget(self._fav_button)
        layout.addWidget(dot)
        layout.addWidget(name_label)
        layout.addWidget(status_label)
        layout.addStretch()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.manage_button)
        self.setLayout(layout)
        self.setFixedHeight(self.sizeHint().height())

    def _toggle_favourite(self):
        self._config.toggle_group_favourite(self.group['name'])
        is_fav = self._config.is_group_favourite(self.group['name'])
        self._fav_button.setText("\u2605" if is_fav else "\u2606")
        if is_fav:
            self._fav_button.setStyleSheet("QPushButton#favBtn { color: #f39c12; }")
        else:
            self._fav_button.setStyleSheet("")

    def _resolve_stacks(self):
        resolved = []
        for member in self.group.get('stacks', []):
            for stack in self._all_stacks:
                if stack.name == member['stackName'] and stack.instance.name == member['instanceName']:
                    resolved.append(stack)
                    break
        return resolved

    def _is_active(self):
        if not self._resolved:
            return False
        return all(s.status is StackStatus.ACTIVE for s in self._resolved)

    def _run_group_action(self, client_fn, predicate):
        targets = [s for s in self._resolved if predicate(s)]
        if not targets:
            return
        self.start_button.start_spinning()
        self.stop_button.start_spinning()
        self._batch_id += 1
        my_batch = self._batch_id
        self._pending = len(targets)
        reload_fn = self.reload_function
        for stack in targets:
            worker = AsyncWorker(client_fn, stack)
            worker.signals.finished.connect(lambda _, b=my_batch: self._on_batch_done(b, reload_fn))
            worker.signals.error.connect(lambda e, b=my_batch: self._on_batch_done(b, reload_fn, e))
            self._pool.start(worker)

    def _on_batch_done(self, batch_id, reload_fn, error_msg=None):
        if batch_id != self._batch_id:
            return
        if error_msg:
            print(f"Group action error: {error_msg}")
        self._pending -= 1
        if self._pending <= 0:
            reload_fn()

    def _start_all(self):
        self._run_group_action(self._client.start_stack, lambda s: s.status is not StackStatus.ACTIVE)

    def _stop_all(self):
        self._run_group_action(self._client.stop_stack, lambda s: s.status is StackStatus.ACTIVE)

    def _manage(self):
        dialog = ManageGroupDialog(self.group, self._all_stacks, self._config, self.window())
        if dialog.exec():
            self.reload_function()


class CreateGroupDialog(QDialog):

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Create Group")
        self.setMinimumWidth(350)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(QLabel("Group name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter group name...")
        layout.addWidget(self.name_input)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        ok_button = QPushButton("Create")
        ok_button.setObjectName("accentBtn")
        ok_button.clicked.connect(self._create)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(ok_button)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def _create(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Group name cannot be empty.")
            return
        for g in self._config.groups:
            if g['name'] == name:
                QMessageBox.warning(self, "Error", f"Group '{name}' already exists.")
                return
        self._config.groups.append({"name": name, "stacks": []})
        self._config.save()
        self.accept()


class ManageGroupDialog(QDialog):

    def __init__(self, group, all_stacks, config, parent=None):
        super().__init__(parent)
        self._group = group
        self._all_stacks = all_stacks
        self._config = config
        self._changed = False

        self.setWindowTitle(f"Manage Group: {group['name']}")
        self.setMinimumWidth(450)
        self.setMinimumHeight(420)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Members</b>"))
        self.members_list = QListWidget()
        self._refresh_members()
        layout.addWidget(self.members_list)

        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._remove_member)
        layout.addWidget(remove_button)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        layout.addWidget(QLabel("<b>Add stack</b>"))
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self.available_combo = QComboBox()
        self.available_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._refresh_available()
        add_row.addWidget(self.available_combo)
        add_button = QPushButton("Add")
        add_button.setObjectName("accentBtn")
        add_button.clicked.connect(self._add_member)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        layout.addStretch()

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        delete_button = QPushButton("Delete Group")
        delete_button.setObjectName("dangerBtn")
        delete_button.clicked.connect(self._delete_group)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self._close)
        bottom.addWidget(delete_button)
        bottom.addStretch()
        bottom.addWidget(close_button)
        layout.addLayout(bottom)

        self.setLayout(layout)

    def _refresh_members(self):
        self.members_list.clear()
        for member in self._group.get('stacks', []):
            item = QListWidgetItem(f"{member['stackName']}  \u2022  {member['instanceName']}")
            item.setData(Qt.ItemDataRole.UserRole, member)
            self.members_list.addItem(item)

    def _refresh_available(self):
        self.available_combo.clear()
        current_members = {
            (m['stackName'], m['instanceName'])
            for m in self._group.get('stacks', [])
        }
        for stack in self._all_stacks:
            key = (stack.name, stack.instance.name)
            if key not in current_members:
                self.available_combo.addItem(
                    f"{stack.name}  \u2022  {stack.instance.name}",
                    {"stackName": stack.name, "instanceName": stack.instance.name}
                )

    def _add_member(self):
        if self.available_combo.count() == 0:
            return
        data = self.available_combo.currentData()
        if 'stacks' not in self._group:
            self._group['stacks'] = []
        self._group['stacks'].append(data)
        self._config.save()
        self._changed = True
        self._refresh_members()
        self._refresh_available()

    def _remove_member(self):
        current = self.members_list.currentItem()
        if not current:
            return
        member = current.data(Qt.ItemDataRole.UserRole)
        self._group['stacks'] = [
            m for m in self._group['stacks']
            if not (m['stackName'] == member['stackName'] and m['instanceName'] == member['instanceName'])
        ]
        self._config.save()
        self._changed = True
        self._refresh_members()
        self._refresh_available()

    def _delete_group(self):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete group '{self._group['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._config.groups[:] = [
                g for g in self._config.groups if g['name'] != self._group['name']
            ]
            self._config.save()
            self._changed = True
            self.accept()

    def _close(self):
        if self._changed:
            self.accept()
        else:
            self.reject()


# --- Tabs ---

class StacksTab(QtWidgets.QWidget):

    stacks_fetched = pyqtSignal(list)

    def __init__(self, client, config, pool):
        super().__init__()
        self._client = client
        self._config = config
        self._pool = pool
        self._fetching = False

        layout = QVBoxLayout()
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        if len(client.instances) > 1:
            cb = QComboBox()
            cb.addItem("All instances")
            for instance in client.instances:
                cb.addItem(instance.name)
            cb.currentTextChanged.connect(self._selectionchange)
            toolbar.addWidget(cb)

        toolbar.addStretch()
        sync_button = QPushButton("\u21bb Refresh")
        sync_button.clicked.connect(self._schedule_fetch)
        toolbar.addWidget(sync_button)
        layout.addLayout(toolbar)

        self._stacks_layout = QVBoxLayout()
        self._stacks_layout.setSpacing(4)

        container = QtWidgets.QWidget()
        container.setLayout(self._stacks_layout)

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        self.setLayout(layout)
        self._schedule_fetch()

        self._timer = QtCore.QTimer()
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._schedule_fetch)
        self._timer.start()

    def _schedule_fetch(self):
        if self._fetching:
            return
        self._fetching = True
        worker = AsyncWorker(self._client.get_stacks)
        worker.signals.finished.connect(self._on_fetch_done)
        worker.signals.error.connect(self._on_fetch_error)
        self._pool.start(worker)

    def _on_fetch_done(self, stacks):
        self._fetching = False
        self._apply_stacks(stacks)

    def _on_fetch_error(self, error_msg):
        self._fetching = False
        print(f"Fetch error: {error_msg}")

    def _apply_stacks(self, stacks):
        _clear_layout(self._stacks_layout)

        favourites = []
        others = []
        for s in stacks:
            if self._config.is_stack_favourite(s.name, s.instance.name):
                favourites.append(s)
            else:
                others.append(s)
        favourites.sort(key=lambda s: s.name.lower())
        others.sort(key=lambda s: s.name.lower())

        if favourites:
            for stack in favourites:
                self._stacks_layout.addWidget(
                    StackItem(stack, self._client, self._pool, self._config, self._schedule_fetch)
                )
            if others:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setObjectName("separator")
                self._stacks_layout.addWidget(sep)

        for stack in others:
            self._stacks_layout.addWidget(
                StackItem(stack, self._client, self._pool, self._config, self._schedule_fetch)
            )

        self._stacks_layout.addStretch()
        self.stacks_fetched.emit(stacks)

    def _selectionchange(self, text):
        for instance in self._client.instances:
            if text == 'All instances':
                instance.active = True
            elif text == instance.name:
                instance.active = True
            else:
                instance.active = False
        self._schedule_fetch()


class GroupsTab(QtWidgets.QWidget):

    def __init__(self, client, config, pool):
        super().__init__()
        self._client = client
        self._config = config
        self._pool = pool
        self._live_stacks = []

        layout = QVBoxLayout()
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        create_button = QPushButton("+ New Group")
        create_button.setObjectName("accentBtn")
        create_button.clicked.connect(self._create_group)
        toolbar.addWidget(create_button)
        layout.addLayout(toolbar)

        self._groups_layout = QVBoxLayout()
        self._groups_layout.setSpacing(4)

        container = QtWidgets.QWidget()
        container.setLayout(self._groups_layout)

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def update_live_stacks(self, stacks):
        self._live_stacks = stacks
        self._rebuild()

    def _rebuild(self):
        _clear_layout(self._groups_layout)

        favourites = []
        others = []
        for g in self._config.groups:
            if self._config.is_group_favourite(g['name']):
                favourites.append(g)
            else:
                others.append(g)
        favourites.sort(key=lambda g: g['name'].lower())
        others.sort(key=lambda g: g['name'].lower())

        if favourites:
            for group in favourites:
                self._groups_layout.addWidget(
                    GroupItem(group, self._live_stacks, self._client, self._pool,
                              self._trigger_refresh, self._config)
                )
            if others:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setObjectName("separator")
                self._groups_layout.addWidget(sep)

        for group in others:
            self._groups_layout.addWidget(
                GroupItem(group, self._live_stacks, self._client, self._pool,
                          self._trigger_refresh, self._config)
            )

        self._groups_layout.addStretch()

    def _trigger_refresh(self):
        worker = AsyncWorker(self._client.get_stacks)
        worker.signals.finished.connect(self._on_refresh)
        worker.signals.error.connect(lambda e: print(f"Group refresh error: {e}"))
        self._pool.start(worker)

    def _on_refresh(self, stacks):
        self._live_stacks = stacks
        self._rebuild()

    def _create_group(self):
        dialog = CreateGroupDialog(self._config, self.window())
        if dialog.exec():
            self._rebuild()


# --- Main Window ---

class MainWindow(QtWidgets.QWidget):

    def __init__(self, config):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Portainer Quick")
        self.setGeometry(500, 200, 650, 520)

        self._config = config
        self._client = PortainerClient(config.instances)
        self._pool = QThreadPool.globalInstance()
        self._force_quit = False
        self._live_stacks = []

        self._stacks_tab = StacksTab(self._client, config, self._pool)
        self._groups_tab = GroupsTab(self._client, config, self._pool)

        self._stacks_tab.stacks_fetched.connect(self._groups_tab.update_live_stacks)
        self._stacks_tab.stacks_fetched.connect(self._update_tray_icon)

        tabs = QTabWidget()
        tabs.addTab(self._stacks_tab, "Stacks")
        tabs.addTab(self._groups_tab, "Groups")

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(tabs)
        self.setLayout(layout)

        self._setup_tray()

    def _setup_tray(self):
        svg_path = _resolve_svg_path()
        self._icon_all_ok = _make_tray_icon(svg_path, all_ok=True)
        self._icon_some_inactive = _make_tray_icon(svg_path, all_ok=False)

        self._tray = QSystemTrayIcon(self._icon_all_ok, self)
        self._tray.setToolTip("Portainer Quick")
        self._tray_menu = QMenu()
        self._tray_menu.aboutToShow.connect(self._populate_tray_menu)
        self._tray.setContextMenu(self._tray_menu)
        self._tray.activated.connect(self._tray_activated)
        self._tray.show()

    def _update_tray_icon(self, stacks):
        self._live_stacks = stacks
        all_ok = bool(stacks) and all(s.status is StackStatus.ACTIVE for s in stacks)
        self._tray.setIcon(self._icon_all_ok if all_ok else self._icon_some_inactive)

    def _populate_tray_menu(self):
        self._tray_menu.clear()
        stacks = self._live_stacks

        fav_stacks = [s for s in stacks if self._config.is_stack_favourite(s.name, s.instance.name)]
        if fav_stacks:
            for stack in fav_stacks:
                status = "\u2705" if stack.status is StackStatus.ACTIVE else "\u274c"
                action_label = "Stop" if stack.status is StackStatus.ACTIVE else "Start"
                action = self._tray_menu.addAction(f"{status} {stack.name}  [{action_label}]")
                action.triggered.connect(lambda checked, s=stack: self._tray_toggle_stack(s))

        fav_groups = [g for g in self._config.groups if self._config.is_group_favourite(g['name'])]
        if fav_groups:
            for group in fav_groups:
                members = self._resolve_group_members(group, stacks)
                active_count = sum(1 for s in members if s.status is StackStatus.ACTIVE)
                total = len(group.get('stacks', []))
                group_sub = self._tray_menu.addMenu(f"\u2b50 {group['name']}  ({active_count}/{total})")
                start_action = group_sub.addAction("\u25b6 Start All")
                start_action.triggered.connect(lambda checked, m=list(members): self._tray_group_start_all(m))
                stop_action = group_sub.addAction("\u23f9 Stop All")
                stop_action.triggered.connect(lambda checked, m=list(members): self._tray_group_stop_all(m))

        if fav_stacks or fav_groups:
            self._tray_menu.addSeparator()

        stacks_menu = self._tray_menu.addMenu("Stacks")
        if stacks:
            for stack in stacks:
                status = "\u2705" if stack.status is StackStatus.ACTIVE else "\u274c"
                action_label = "Stop" if stack.status is StackStatus.ACTIVE else "Start"
                action = stacks_menu.addAction(f"{status} {stack.name}  \u2022  {stack.instance.name}  [{action_label}]")
                action.triggered.connect(lambda checked, s=stack: self._tray_toggle_stack(s))
        else:
            stacks_menu.addAction("(no stacks)").setEnabled(False)

        groups_menu = self._tray_menu.addMenu("Groups")
        if self._config.groups:
            for group in self._config.groups:
                members = self._resolve_group_members(group, stacks)
                active_count = sum(1 for s in members if s.status is StackStatus.ACTIVE)
                total = len(group.get('stacks', []))
                group_sub = groups_menu.addMenu(f"{group['name']}  ({active_count}/{total})")
                start_action = group_sub.addAction("\u25b6 Start All")
                start_action.triggered.connect(lambda checked, m=list(members): self._tray_group_start_all(m))
                stop_action = group_sub.addAction("\u23f9 Stop All")
                stop_action.triggered.connect(lambda checked, m=list(members): self._tray_group_stop_all(m))
        else:
            groups_menu.addAction("(no groups)").setEnabled(False)

        self._tray_menu.addSeparator()
        show_action = self._tray_menu.addAction("Show/Hide")
        show_action.triggered.connect(self._toggle_window)
        quit_action = self._tray_menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

    def _resolve_group_members(self, group, stacks):
        members = []
        for member in group.get('stacks', []):
            for s in stacks:
                if s.name == member['stackName'] and s.instance.name == member['instanceName']:
                    members.append(s)
                    break
        return members

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window()

    def _toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _tray_toggle_stack(self, stack):
        if stack.status is StackStatus.ACTIVE:
            worker = AsyncWorker(self._client.stop_stack, stack)
        else:
            worker = AsyncWorker(self._client.start_stack, stack)
        worker.signals.finished.connect(lambda _: self._stacks_tab._schedule_fetch())
        worker.signals.error.connect(lambda e: print(f"Tray stack action error: {e}"))
        self._pool.start(worker)

    def _tray_group_start_all(self, members):
        targets = [s for s in members if s.status is not StackStatus.ACTIVE]
        self._tray_dispatch_batch(targets, self._client.start_stack)

    def _tray_group_stop_all(self, members):
        targets = [s for s in members if s.status is StackStatus.ACTIVE]
        self._tray_dispatch_batch(targets, self._client.stop_stack)

    def _tray_dispatch_batch(self, targets, client_fn):
        if not targets:
            return
        pending = [len(targets)]

        def on_done(_):
            pending[0] -= 1
            if pending[0] <= 0:
                self._stacks_tab._schedule_fetch()

        def on_error(e):
            print(f"Tray group action error: {e}")
            pending[0] -= 1
            if pending[0] <= 0:
                self._stacks_tab._schedule_fetch()

        for stack in targets:
            worker = AsyncWorker(client_fn, stack)
            worker.signals.finished.connect(on_done)
            worker.signals.error.connect(on_error)
            self._pool.start(worker)

    def closeEvent(self, event):
        if self._force_quit:
            self._tray.hide()
            event.accept()
        else:
            event.ignore()
            self.hide()

    def _quit(self):
        self._force_quit = True
        QtWidgets.QApplication.quit()


# --- Entry Point ---

def main():
    config = AppConfig.load()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    app.setQuitOnLastWindowClosed(False)
    win = MainWindow(config)
    sys.exit(app.exec())


main()
