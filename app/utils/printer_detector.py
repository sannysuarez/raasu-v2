"""Thermal printer detection module using PySerial and PyUSB"""
import serial
import usb.core
import usb.util
from typing import List, Dict, Optional

class PrinterDetector:
    """Detect and manage thermal printers via USB and Serial ports"""
    
    # Common thermal printer vendor IDs
    THERMAL_PRINTER_VENDORS = {
        0x04b8: 'Epson',
        0x0483: 'STMicroelectronics',
        0x067b: 'Prolific',
        0x10c4: 'Silicon Labs',
        0x0658: 'Sigma Designs',
    }
    
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
    def detect_serial_printers() -> List[Dict[str, str]]:
        """Detect serial/Bluetooth thermal printers"""
        printers = []
        
        try:
            # Try common serial ports
            common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2',  # Linux
                          '/dev/ttyACM0', '/dev/ttyACM1',  # Arduino-like devices
                          'COM1', 'COM2', 'COM3', 'COM4', 'COM5']  # Windows
            
            for port in common_ports:
                try:
                    ser = serial.Serial(port, timeout=0.5)
                    ser.close()
                    printers.append({
                        'type': 'Serial/Bluetooth',
                        'port': port,
                        'description': f'Serial Port: {port}'
                    })
                except:
                    pass
        except Exception as e:
            print(f"Error detecting serial printers: {e}")
        
        return printers
    
    @staticmethod
    def get_all_printers() -> List[Dict[str, str]]:
        """Get all detected printers (USB + Serial)"""
        printers = []
        printers.extend(PrinterDetector.detect_usb_printers())
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
            else:
                # Serial printer detection
                ser = serial.Serial(printer_info['port'], timeout=1)
                ser.close()
                return True
        except Exception as e:
            print(f"Error testing printer connection: {e}")
            return False
