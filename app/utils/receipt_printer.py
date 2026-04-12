"""Receipt printing module for thermal printers"""
import serial
from datetime import datetime
from typing import List, Dict, Optional

try:
    import bluetooth  # PyBluez - may not be available on all platforms
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    print("PyBluez not available. Bluetooth printing disabled.")

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False
    print("PyUSB not available. USB printing disabled.")

class ThermalReceiptPrinter:
    """Handle receipt printing to thermal printers"""
    
    # ESC/POS Commands
    ESC = b'\x1b'
    GS = b'\x1d'
    
    # Print modes
    ALIGN_LEFT = 0x00
    ALIGN_CENTER = 0x01
    ALIGN_RIGHT = 0x02
    
    TEXT_NORMAL = 0x00
    TEXT_BOLD = 0x08
    TEXT_DOUBLE_HEIGHT = 0x10
    TEXT_DOUBLE_WIDTH = 0x20
    
    def __init__(self, port=None, bluetooth_addr=None, usb_vendor_id=None, usb_product_id=None):
        """Initialize printer connection"""
        self.port = port
        self.bluetooth_addr = bluetooth_addr
        self.usb_vendor_id = usb_vendor_id
        self.usb_product_id = usb_product_id
        self.serial = None
        self.bt_sock = None
        self.usb_device = None
        self.usb_endpoint = None
        self.width = 32  # Standard thermal printer width in characters
    
    def connect(self, port: str = None, bluetooth_addr: str = None, usb_vendor_id: int = None, usb_product_id: int = None, baudrate: int = 9600) -> bool:
        """Connect to thermal printer via serial, Bluetooth, or USB"""
        if usb_vendor_id is not None and usb_product_id is not None and USB_AVAILABLE:
            try:
                self.usb_device = usb.core.find(idVendor=usb_vendor_id, idProduct=usb_product_id)
                if self.usb_device is None:
                    return False
                
                # Set configuration
                self.usb_device.set_configuration()
                
                # Get the active configuration
                cfg = self.usb_device.get_active_configuration()
                
                # Find the bulk out endpoint
                interface = cfg[(0, 0)]
                self.usb_endpoint = usb.util.find_descriptor(
                    interface,
                    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
                )
                
                if self.usb_endpoint is None:
                    return False
                
                self.usb_vendor_id = usb_vendor_id
                self.usb_product_id = usb_product_id
                return True
            except Exception as e:
                print(f"Failed to connect to USB printer {usb_vendor_id}:{usb_product_id}: {e}")
                return False
        elif bluetooth_addr and BLUETOOTH_AVAILABLE:
            try:
                self.bt_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.bt_sock.connect((bluetooth_addr, 1))  # RFCOMM channel 1 for SPP
                self.bluetooth_addr = bluetooth_addr
                return True
            except Exception as e:
                print(f"Failed to connect to Bluetooth {bluetooth_addr}: {e}")
                return False
        elif port:
            try:
                self.serial = serial.Serial(port, baudrate, timeout=1)
                self.port = port
                return True
            except Exception as e:
                print(f"Failed to connect to {port}: {e}")
                return False
        return False
    
    def disconnect(self):
        """Disconnect from printer"""
        if self.serial:
            self.serial.close()
            self.serial = None
        if self.bt_sock and BLUETOOTH_AVAILABLE:
            self.bt_sock.close()
            self.bt_sock = None
        if self.usb_device and USB_AVAILABLE:
            usb.util.dispose_resources(self.usb_device)
            self.usb_device = None
            self.usb_endpoint = None
    
    def write(self, data: bytes):
        """Send data to printer"""
        if self.serial and self.serial.is_open:
            self.serial.write(data)
        elif self.bt_sock and BLUETOOTH_AVAILABLE:
            self.bt_sock.send(data)
        elif self.usb_endpoint and USB_AVAILABLE:
            self.usb_endpoint.write(data)
    
    def reset(self):
        """Reset printer to default settings"""
        self.write(self.ESC + b'@')
    
    def set_alignment(self, alignment: int):
        """Set text alignment (0=left, 1=center, 2=right)"""
        self.write(self.ESC + b'a' + bytes([alignment]))
    
    def print_text(
            self,
            text: str,
            align: int = ALIGN_LEFT,
            bold: bool = False,
            width: int = 1,
            height: int =1,
            font: str = "A" # 'A' = normal, 'B' = small font
    ):
        """Print text with optional formatting"""
        #-----------------------
        # Alignment
        #-----------------------
        self.set_alignment(align)

        #-----------------------
        # Bold
        #-----------------------
        if bold:
            self.write(self.ESC + b'E' + b'\x01')  # Bold on

        #-----------------------
        # Font Selection
        #-----------------------
        # ESC M n -> n = 0: Font A, 1: Font B
        if font.upper() == "B":
            self.write(b'\x1B\x4D\x01') # Font B (small)
        else:
            self.write(b'\x1B\x4D\x00') # Font A (default)

        #------------------------
        # Width & Height Scaling
        #------------------------
        # GS ! n -> Width/height scaling
        scale = 0x00

        if width == 2:
            scale |= 0x200 # double width
        if height ==2:
            scale |= 0x10 # double height
        self.write(b'\x1D\x21' + bytes([scale]))
        
        #---------------------------
        # Write the text
        #---------------------------
        lines = self._wrap_text(text, self.width)
        for line in lines:
            self.write((line + '\n').encode('utf-8'))

        #--------------------------
        # Reset scaling & bold
        #--------------------------
        self.write(b'\x1D\x21\x00') # reset scale to normal
        self.write(self.ESC + b'E' + b'\x00') # bold off

    
    def print_revenue_receipt(self, venture_name: str, address: str, 
                             items: List[Dict], total: float, 
                             user_name: str, date: datetime = None):
        """Print a complete revenue receipt"""
        if date is None:
            date = datetime.now()
        
        
        self.reset()
        # Header
        self.print_text("RA'ASU VENTURES", align=self.ALIGN_CENTER, bold=True, height=2)
        self.print_text("Ceramics, trailer park", align=self.ALIGN_CENTER)
        self.print_text("Ajaokuta", align=self.ALIGN_CENTER)
        self.print_text("08065808288 - 08080626221", align=self.ALIGN_CENTER)
        self.print_text("-" * self.width)
        
        # Receipt info
        self.print_text(f"Date: {date.strftime('%Y-%m-%d %H:%M:%S')}", align=self.ALIGN_LEFT)
        self.print_text(f"User: {user_name}", align=self.ALIGN_LEFT)
        self.print_text("-" * self.width)
        
       
       
        # Items header
        header = f"Product{'--------'}Qty{'-----'}price"
        self.print_text(header, align=self.ALIGN_LEFT, bold=True)

        self.print_text("-" * self.width)
        
        
        # Items
    
        for item in items:
            product_name = item['product_name'][:15]
            qty =  item['quantity']
            price = item['price']
            
            
            line = f"{product_name} {qty} {price:,.0f}"
            self.print_text(line, align=self.ALIGN_LEFT)
        
        self.print_text("-" * self.width)
        
        # Total
        total_line = f"{'TOTAL:':<15} {total:>17,.0f}"
        self.print_text(total_line, align=self.ALIGN_LEFT, bold=True)
        
        # Footer
        self.print_text("-" * self.width)
        self.print_text("Thank You!", align=self.ALIGN_CENTER, bold=True)
        self.print_text("")
        self.print_text("Developer:", align=self.ALIGN_CENTER)
        self.print_text("sanni.com.ng", align=self.ALIGN_CENTER, bold=True)
        
        
        # Cut paper
        self.write(self.GS + b'V' + b'\x41' + b'\x03')  # Partial cut
        
        # Feed lines
        for _ in range(2):
            self.write(b'\n')
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to fit printer width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines if lines else [""]
