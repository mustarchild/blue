from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.toast import toast
from kivy.clock import Clock
from jnius import autoclass
from android.permissions import request_permissions, Permission

layout = '''

BoxLayout:
    orientation:'vertical'
    padding: 10
    spacing: 10

    MDIconButton:
        icon: "bluetooth"
        pos_hint: {'center_x':0.5}
        user_font_size: "40sp"
        on_release: app.connect_bluetooth()

    ScrollView:
        GridLayout:
            id: grid
            cols: 2
            size_hint_y: None
            height: self.minimum_height
            row_default_height: 60
            spacing: 10

    MDRaisedButton:
        text: "SAVE BMS PARAMETERS"
        size_hint_y: None
        height: 60
        on_release: app.send_bms_data()
'''

class AndroidBluetoothClass:

    def __init__(self):
        self.BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        self.UUID = autoclass('java.util.UUID')
        self.BufferReader = autoclass('java.io.BufferedReader')
        self.InputStream = autoclass('java.io.InputStreamReader')
        self.ConnectionEstablished = False

    def connect(self, DeviceName):
        paired_devices = self.BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
        for device in paired_devices:
            if device.getName() == DeviceName:
                socket = device.createRfcommSocketToServiceRecord(
                    self.UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                socket.connect()
                self.SendData = socket.getOutputStream()
                self.ReceiveData = self.BufferReader(self.InputStream(socket.getInputStream()))
                self.ConnectionEstablished = True
                toast("Bluetooth Connected")
                return True
        toast("Device Not Found")
        return False

    def send(self, message):
        if self.ConnectionEstablished:
            self.SendData.write(message.encode())

    def receive(self):
        if self.ConnectionEstablished:
            return str(self.ReceiveData.readline())
        return None


class TestApp(MDApp):

    def build(self):

        request_permissions([
            Permission.BLUETOOTH_ADMIN,
            Permission.BLUETOOTH,
            Permission.BLUETOOTH_CONNECT,
            Permission.BLUETOOTH_SCAN
        ])

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"

        self.bt = AndroidBluetoothClass()
        root = Builder.load_string(layout)

        from kivymd.uix.label import MDLabel
        from kivymd.uix.textfield import MDTextField

        self.dashboard_fields = {}
        self.bms_fields = {}

        # ------------------ DASHBOARD (READ ONLY) ------------------

        dashboard_items = [
            "Peak Voltage","Peak Current","Temperature","SOC",
            "Cell1","Cell2","Cell3","Cell4","Cell5","Cell6","Cell7","Cell8",
            "Cell9","Cell10","Cell11","Cell12","Cell13","Cell14","Cell15","Cell16"
        ]

        root.ids.grid.add_widget(MDLabel(text="--- DASHBOARD (READ ONLY) ---"))
        root.ids.grid.add_widget(MDLabel(text=""))

        for item in dashboard_items:
            root.ids.grid.add_widget(MDLabel(text=item))
            field = MDTextField(readonly=True)
            self.dashboard_fields[item] = field
            root.ids.grid.add_widget(field)

        # ------------------ BMS PARAMETERS (SEND + RECEIVE) ------------------

        bms_items = [
            "Over Voltage Limit",
            "Under Voltage Limit",
            "Over Current Limit",
            "Temperature Limit"
        ]

        root.ids.grid.add_widget(MDLabel(text="--- BMS PARAMETERS ---"))
        root.ids.grid.add_widget(MDLabel(text=""))

        for item in bms_items:
            root.ids.grid.add_widget(MDLabel(text=item))
            field = MDTextField()
            self.bms_fields[item] = field
            root.ids.grid.add_widget(field)

        return root


    # ------------------ BLUETOOTH CONNECT ------------------

    def connect_bluetooth(self):
        if self.bt.connect("rasp"):
            Clock.schedule_interval(self.read_data, 1)


    # ------------------ RECEIVE DATA ------------------

    def read_data(self, dt):
        data = self.bt.receive()
        if data:
            try:
                values = data.strip().split(",")

                keys = list(self.dashboard_fields.keys())
                for i in range(min(len(values), len(keys))):
                    self.dashboard_fields[keys[i]].text = values[i]

            except:
                pass


    # ------------------ SEND ONLY BMS PARAMETERS ------------------

    def send_bms_data(self):

        data_string = ""
        for key in self.bms_fields:
            value = self.bms_fields[key].text
            data_string += value + ","

        data_string = "BMS:" + data_string[:-1] + "\n"

        print("Sending:", data_string)
        self.bt.send(data_string)
        toast("BMS Parameters Sent")


TestApp().run()
