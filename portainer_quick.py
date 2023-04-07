from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMessageBox, QPushButton
from enum import Enum
import sys
import json
from types import SimpleNamespace
import requests
import os
from pathlib import Path


class StackStatus(Enum):
    ACTIVE = 1
    INACTIVE = 2


class Stack:

    def __init__(self, name, status, id, instance):
        self.name = name
        self.id = id
        self.instance = instance
        if status == 1:
            self.status = StackStatus.ACTIVE
        else:
            self.status = StackStatus.INACTIVE


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
                response = requests.get(url, headers=headers, verify = False)
                list = response.json()
                for stack in list:
                    stacks.append(Stack(stack['Name'], stack['Status'], stack['Id'], instance))
        return stacks

    def start_stack(self, stack: Stack):
        url = f'{stack.instance.url}/api/stacks/{stack.id}/start'
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': stack.instance.apiKey
        }
        response = requests.post(url, headers=headers, verify = False)
        return response

    def stop_stack(self, stack: Stack):
        url = f'{stack.instance.url}/api/stacks/{stack.id}/stop'
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': stack.instance.apiKey
        }
        response = requests.post(url, headers=headers, verify = False)
        return response



class StackItem(QtWidgets.QWidget):
    def __init__(self, stack: Stack, reload_function):
        super().__init__()
        self.stack = stack
        self.reload_function = reload_function
        label = "START"
        if stack.status is StackStatus.ACTIVE:
            label = "STOP"
        self.button = QPushButton(label)
        self.button.clicked.connect(self.button_clicked)
        self.labelWidget = QtWidgets.QLabel(stack.name + " @ " +stack.instance.name)
        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.addWidget(self.labelWidget)
        horizontalLayout.addWidget(self.button)
        if stack.status is StackStatus.ACTIVE:
            self.button.setStyleSheet("background-color: red;")
        else:
            self.button.setStyleSheet("background-color: green;")
        self.setLayout(horizontalLayout)

    def button_clicked(self):
        print(f"Clicked action button for stack {self.stack.id}")
        if self.stack.status is StackStatus.ACTIVE:
            client.stop_stack(self.stack)
        else:
            client.start_stack(self.stack)
        message = QMessageBox(self)
        message.setWindowTitle("Stack status change")
        message.setText(
            f"{self.stack.name} has {'started' if self.stack.status is StackStatus.INACTIVE else 'stopped'}!")
        message.show()
        self.reload_function()


class window(QtWidgets.QWidget):
    def __init__(self, client):
        super().__init__()
        self.setWindowTitle("Portainer quick client")
        self.setGeometry(500, 200, 500, 400)
        self.stacksLayout = QtWidgets.QVBoxLayout()
        groupBox = QtWidgets.QGroupBox("Available stacks")
        groupBox.setLayout(self.stacksLayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(400)

        vbox = QtWidgets.QVBoxLayout()
        syncButton = QtWidgets.QPushButton("Sync")
        syncButton.clicked.connect(self.sync_clicked)

        cb = QtWidgets.QComboBox()
        cb.addItem("All")
        for instance in client.instances:
            cb.addItem(instance.name)
        cb.currentTextChanged.connect(self.selectionchange)


        vbox.addWidget(cb)
        vbox.addWidget(syncButton)
        vbox.addWidget(scroll)

        self.window().setLayout(vbox)
        self.reload_stacks()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.reload_stacks)
        self.timer.start()

    def reload_stacks(self):
        stacks = client.get_stacks()
        for i in reversed(range(self.stacksLayout.count())):
            self.stacksLayout.itemAt(i).widget().setParent(None)
        for stack in stacks:
            print(f"Stack {stack.name} with id {stack.id} is in status {stack.status}")
            containerItem = StackItem(stack, lambda: self.sync_clicked())
            self.stacksLayout.addWidget(containerItem)

    def sync_clicked(self):
        print(f"Sync clicked")
        self.reload_stacks()

    def selectionchange(self,i):
        for instance in client.instances:
            if i == 'All':
                instance.active = True
            elif i == instance.name:
                instance.active = True
            else:
                instance.active = False
        self.reload_stacks()

def app(client):
    app = QtWidgets.QApplication(sys.argv)
    win = window(client)
    win.show()
    sys.exit(app.exec())


config_folder_path = Path.home().__str__() + '/.config/portainer-quick'
config_path = config_folder_path + '/config.json'
if not os.path.exists(config_folder_path):
    os.makedirs(config_folder_path)
if not os.path.isfile(config_path):
    with open(config_path, 'w') as config_file:
        json = '''
        {
            "name":"Example",
            "url": "http://localhost:9000",
            "apiKey": ""
        }
        '''
        config_file.write(json)
        print("Config file created")
        exit(1)

with open(config_path) as config_file:
    print(config_file.name)
    configs = json.load(config_file)
    instances = json.loads(json.dumps(configs['instances']), object_hook=lambda d: SimpleNamespace(**d))
    for instance in instances:
        instance.active = True
        if instance.apiKey == '' or instance.url == '' or instance.name == '':
            print(instance)
            print("Api key or url not defined")
            exit(1)
    client = PortainerClient(instances) 
    
app(client)
