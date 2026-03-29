"""Receipt printing module for thermal printers"""
import serial
from datetime import datetime
from typing import List, Dict, Optional

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
    
    def __init__(self, port=None):
        """Initialize printer connection"""
        self.port = port
        self.serial = None
        self.width = 32  # Standard thermal printer width in characters
    
    def connect(self, port: str, baudrate: int = 9600) -> bool:
        """Connect to thermal printer"""
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
            self.port = port
            return True
        except Exception as e:
            print(f"Failed to connect to {port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from printer"""
        if self.serial:
            self.serial.close()
            self.serial = None
    
    def write(self, data: bytes):
        """Send data to printer"""
        if self.serial and self.serial.is_open:
            self.serial.write(data)
    
    def reset(self):
        """Reset printer to default settings"""
        self.write(self.ESC + b'@')
    
    def set_alignment(self, alignment: int):
        """Set text alignment (0=left, 1=center, 2=right)"""
        self.write(self.ESC + b'a' + bytes([alignment]))
    
    def print_text(self, text: str, align: int = ALIGN_LEFT, bold: bool = False):
        """Print text"""
        self.set_alignment(align)
        
        if bold:
            self.write(self.ESC + b'E' + b'\x01')  # Bold on
        
        # Wrap text to printer width
        lines = self._wrap_text(text, self.width)
        for line in lines:
            self.write((line + '\n').encode('utf-8'))
        
        if bold:
            self.write(self.ESC + b'E' + b'\x00')  # Bold off
    
    def print_line(self, char: str = '-'):
        """Print a line separator"""
        self.write((char * self.width + '\n').encode('utf-8'))
    
    def print_revenue_receipt(self, venture_name: str, address: str, 
                             items: List[Dict], total: float, 
                             user_name: str, date: datetime = None):
        """Print a complete revenue receipt"""
        if date is None:
            date = datetime.now()
        
        self.reset()
        
        # Header
        self.print_text("Ra'asu Ventures", align=self.ALIGN_CENTER, bold=True)
        self.print_text(address, align=self.ALIGN_CENTER)
        self.print_line()
        
        # Receipt info
        self.print_text(f"Date: {date.strftime('%Y-%m-%d %H:%M:%S')}", align=self.ALIGN_LEFT)
        self.print_text(f"User: {user_name}", align=self.ALIGN_LEFT)
        self.print_line()
        
        # Items header
        header = f"{'Product':<15} {'Qty':>4} {'Price':>6} {'Total':>6}"
        self.print_text(header, align=self.ALIGN_LEFT, bold=True)
        self.print_line()
        
        # Items
        for item in items:
            product_name = item['product_name'][:15]
            qty = item['quantity']
            price = item['price']
            item_total = qty * price
            
            line = f"{product_name:<15} {qty:>4} ₦{price:>6,.0f} ₦{item_total:>6,.0f}"
            self.print_text(line, align=self.ALIGN_LEFT)
        
        self.print_line()
        
        # Total
        total_line = f"₦{'TOTAL':<15} ₦{total:>17,.0f}"
        self.print_text(total_line, align=self.ALIGN_LEFT, bold=True)
        
        # Footer
        self.print_line()
        self.print_text("Thank You!", align=self.ALIGN_CENTER, bold=True)
        
        # Cut paper
        self.write(self.GS + b'V' + b'\x41' + b'\x03')  # Partial cut
        
        # Feed lines
        for _ in range(3):
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
