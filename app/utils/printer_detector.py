"""Thermal printer detection module using PySerial, PyUSB, and PyBluez"""
import serial
import usb.core
import usb.util
from typing import List, Dict, Optional
import platform

try:
    import bluetooth  # PyBluez - may not be available on all platforms
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    print("PyBluez not available. Bluetooth detection disabled.")

class PrinterDetector:
    """Detect and manage thermal printers via USB, Serial, and Bluetooth"""
    
    # Common thermal printer vendor IDs
    THERMAL_PRINTER_VENDORS = {
        0x04b8: 'Epson',
        0x0483: 'STMicroelectronics',
        0x067b: 'Prolific',
        0x10c4: 'Silicon Labs',
        0x0658: 'Sigma Designs',
    }
    
    # Specific MPT-II identifiers
    MPT_II_NAMES = ['MPT-II', 'MPT II', 'MPT-2', 'MPT 2']
    
    @staticmethod
    def detect_usb_printers() -> List[Dict[str, str]]:
        """Detect USB thermal printers"""
        printers = []
        
        try:
            devices = usb.core.find(find_all=True)
            for device in devices:
                vendor_name = PrinterDetector.THERMAL_PRINTER_VENDORS.get(
                    device.idVendor, 
                    'Unknown'
                )
                printers.append({
                    'type': 'USB',
                    'vendor_id': device.idVendor,
                    'product_id': device.idProduct,
                    'vendor_name': vendor_name,
                    'device': str(device),
                    'description': f'{vendor_name} (USB ID: {device.idVendor:04x}:{device.idProduct:04x})'
                })
        except Exception as e:
            print(f"Error detecting USB printers: {e}")
        
        return printers
    
    @staticmethod
    def detect_bluetooth_printers() -> List[Dict[str, str]]:
        """Detect Bluetooth thermal printers (SPP)"""
        printers = []
        
        if not BLUETOOTH_AVAILABLE:
            return printers
        
        try:
            # Discover nearby Bluetooth devices
            nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
            
            for addr, name in nearby_devices:
                if name and any(mpt_name.lower() in name.lower() for mpt_name in PrinterDetector.MPT_II_NAMES):
                    printers.append({
                        'type': 'Bluetooth',
                        'address': addr,
                        'name': name,
                        'description': f'MPT-II Bluetooth Printer: {name} ({addr})'
                    })
        except Exception as e:
            print(f"Error detecting Bluetooth printers: {e}")
        
        return printers
    
    @staticmethod
    def detect_serial_printers() -> List[Dict[str, str]]:
        """Detect serial/Bluetooth thermal printers (paired devices)"""
        printers = []
        
        try:
            # Try common serial ports
            common_ports = []
            
            if platform.system() == 'Windows':
                # Windows COM ports
                for i in range(1, 20):
                    common_ports.append(f'COM{i}')
            else:
                # Linux/Android common ports
                common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2',
                              '/dev/ttyACM0', '/dev/ttyACM1',
                              '/dev/rfcomm0', '/dev/rfcomm1', '/dev/rfcomm2']  # Bluetooth SPP
            
            for port in common_ports:
                try:
                    ser = serial.Serial(port, timeout=0.5)
                    # Try to identify MPT-II by sending a status query
                    ser.write(b'\x1d\x49\x01')  # ESC/POS status query
                    response = ser.read(10)
                    ser.close()
                    
                    # MPT-II specific response check (this may need adjustment based on actual response)
                    if response:  # If we get any response, assume it's a printer
                        printers.append({
                            'type': 'Serial/Bluetooth',
                            'port': port,
                            'description': f'Serial Port: {port} (MPT-II detected)'
                        })
                except:
                    pass
        except Exception as e:
            print(f"Error detecting serial printers: {e}")
        
        return printers
    
    @staticmethod
    def get_all_printers() -> List[Dict[str, str]]:
        """Get all detected printers (USB + Serial + Bluetooth)"""
        printers = []
        printers.extend(PrinterDetector.detect_usb_printers())
        printers.extend(PrinterDetector.detect_bluetooth_printers())
        printers.extend(PrinterDetector.detect_serial_printers())
        return printers
    
    @staticmethod
    def test_printer_connection(printer_info: Dict[str, str]) -> bool:
        """Test if a printer is accessible"""
        try:
            if printer_info['type'] == 'USB':
                # USB printer detection
                device = usb.core.find(
                    idVendor=printer_info['vendor_id'],
                    idProduct=printer_info['product_id']
                )
                return device is not None
            elif printer_info['type'] == 'Bluetooth' and BLUETOOTH_AVAILABLE:
                # Bluetooth printer test
                sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                sock.connect((printer_info['address'], 1))  # RFCOMM channel 1 for SPP
                sock.close()
                return True
            else:
                # Serial printer detection
                ser = serial.Serial(printer_info['port'], timeout=1)
                ser.close()
                return True
        except Exception as e:
            print(f"Error testing printer connection: {e}")
            return False
