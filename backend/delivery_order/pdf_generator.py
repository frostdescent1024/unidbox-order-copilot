"""
PDF Generator Module for UnidBox Order Copilot

This module generates PDF documents for Delivery Orders using
ReportLab or similar PDF generation libraries.
"""

import io
from typing import Optional, Dict, Any
from datetime import datetime

from .do_generator import DeliveryOrder, DOItem


class PDFGenerator:
    """
    Generates PDF documents for Delivery Orders.
    
    Uses ReportLab for PDF generation with professional formatting.
    Falls back to HTML-to-PDF if ReportLab is not available.
    """
    
    # Page dimensions (A4)
    PAGE_WIDTH = 595.27
    PAGE_HEIGHT = 841.89
    MARGIN = 50
    
    # Colors
    PRIMARY_COLOR = (30, 58, 95)  # Navy blue RGB
    SECONDARY_COLOR = (245, 158, 11)  # Amber RGB
    TEXT_COLOR = (31, 41, 55)  # Dark gray RGB
    LIGHT_GRAY = (243, 244, 246)
    
    def __init__(self):
        """Initialize the PDF generator"""
        self._reportlab_available = self._check_reportlab()
    
    def _check_reportlab(self) -> bool:
        """Check if ReportLab is available"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            return True
        except ImportError:
            return False
    
    def generate(self, do: DeliveryOrder) -> bytes:
        """
        Generate a PDF for the Delivery Order.
        
        Args:
            do: DeliveryOrder object
            
        Returns:
            PDF content as bytes
        """
        if self._reportlab_available:
            return self._generate_reportlab(do)
        else:
            return self._generate_html_pdf(do)
    
    def _generate_reportlab(self, do: DeliveryOrder) -> bytes:
        """Generate PDF using ReportLab"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Helper function for colors
        def rgb_color(r, g, b):
            return colors.Color(r/255, g/255, b/255)
        
        primary = rgb_color(*self.PRIMARY_COLOR)
        secondary = rgb_color(*self.SECONDARY_COLOR)
        text_color = rgb_color(*self.TEXT_COLOR)
        light_gray = rgb_color(*self.LIGHT_GRAY)
        
        y = height - self.MARGIN
        
        # Header
        c.setFillColor(primary)
        c.rect(0, height - 100, width, 100, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(self.MARGIN, height - 50, "DELIVERY ORDER")
        
        c.setFont("Helvetica", 10)
        c.drawString(self.MARGIN, height - 70, "UnidBox Hardware Pte. Ltd.")
        
        # DO Number and Date (right side)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - self.MARGIN, height - 50, f"DO#: {do.do_number}")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - self.MARGIN, height - 70, f"Date: {do.issue_date}")
        
        y = height - 130
        
        # Ship From / Ship To boxes
        box_width = (width - 3 * self.MARGIN) / 2
        
        # Ship From
        c.setFillColor(light_gray)
        c.rect(self.MARGIN, y - 80, box_width, 80, fill=True, stroke=False)
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN + 10, y - 15, "SHIP FROM")
        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN + 10, y - 30, do.ship_from.name)
        if do.ship_from.address_line1:
            c.drawString(self.MARGIN + 10, y - 42, do.ship_from.address_line1)
        if do.ship_from.address_line2:
            c.drawString(self.MARGIN + 10, y - 54, do.ship_from.address_line2)
        c.drawString(self.MARGIN + 10, y - 66, f"{do.ship_from.city} {do.ship_from.postal_code or ''}")
        
        # Ship To
        ship_to_x = self.MARGIN + box_width + self.MARGIN
        c.setFillColor(light_gray)
        c.rect(ship_to_x, y - 80, box_width, 80, fill=True, stroke=False)
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(ship_to_x + 10, y - 15, "SHIP TO")
        c.setFont("Helvetica", 9)
        c.drawString(ship_to_x + 10, y - 30, do.ship_to.name)
        if do.ship_to.address_line1:
            c.drawString(ship_to_x + 10, y - 42, do.ship_to.address_line1)
        if do.ship_to.phone:
            c.drawString(ship_to_x + 10, y - 54, f"Tel: {do.ship_to.phone}")
        if do.ship_to.email:
            c.drawString(ship_to_x + 10, y - 66, do.ship_to.email)
        
        y -= 100
        
        # Order details
        c.setFillColor(text_color)
        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN, y, f"Order ID: {do.order_id}")
        c.drawString(self.MARGIN + 200, y, f"Delivery Date: {do.delivery_date or 'TBD'}")
        c.drawString(self.MARGIN + 400, y, f"Terms: {do.payment_terms}")
        
        y -= 30
        
        # Items table
        table_data = [["#", "Product", "Description", "Qty", "Unit Price", "Total"]]
        
        for item in do.items:
            table_data.append([
                str(item.line_number),
                item.product_name[:30] + "..." if len(item.product_name) > 30 else item.product_name,
                (item.description or "")[:20],
                str(item.quantity),
                f"${item.unit_price:.2f}",
                f"${item.total_price:.2f}"
            ])
        
        col_widths = [30, 180, 100, 40, 70, 70]
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_gray]),
        ]))
        
        table_width, table_height = table.wrap(0, 0)
        table.drawOn(c, self.MARGIN, y - table_height)
        
        y = y - table_height - 30
        
        # Totals
        totals_x = width - self.MARGIN - 150
        c.setFont("Helvetica", 9)
        c.drawString(totals_x, y, "Subtotal:")
        c.drawRightString(width - self.MARGIN, y, f"${do.subtotal:.2f}")
        
        y -= 15
        c.drawString(totals_x, y, f"GST ({do.tax_rate*100:.0f}%):")
        c.drawRightString(width - self.MARGIN, y, f"${do.tax_amount:.2f}")
        
        y -= 15
        c.drawString(totals_x, y, "Shipping:")
        c.drawRightString(width - self.MARGIN, y, f"${do.shipping_cost:.2f}")
        
        y -= 20
        c.setFillColor(primary)
        c.rect(totals_x - 10, y - 5, 160, 20, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(totals_x, y, "TOTAL:")
        c.drawRightString(width - self.MARGIN, y, f"${do.total:.2f} {do.currency}")
        
        y -= 50
        
        # Special instructions
        if do.special_instructions:
            c.setFillColor(text_color)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(self.MARGIN, y, "Special Instructions:")
            c.setFont("Helvetica", 9)
            c.drawString(self.MARGIN, y - 15, do.special_instructions[:100])
            y -= 40
        
        # Signature section
        y = 120
        sig_width = (width - 4 * self.MARGIN) / 3
        
        c.setFillColor(text_color)
        c.setFont("Helvetica", 8)
        
        # Prepared by
        c.line(self.MARGIN, y, self.MARGIN + sig_width, y)
        c.drawString(self.MARGIN, y - 12, "Prepared By")
        if do.prepared_by:
            c.drawString(self.MARGIN, y + 10, do.prepared_by)
        
        # Approved by
        c.line(self.MARGIN + sig_width + self.MARGIN/2, y, self.MARGIN + 2*sig_width + self.MARGIN/2, y)
        c.drawString(self.MARGIN + sig_width + self.MARGIN/2, y - 12, "Approved By")
        
        # Received by
        c.line(self.MARGIN + 2*sig_width + self.MARGIN, y, self.MARGIN + 3*sig_width + self.MARGIN, y)
        c.drawString(self.MARGIN + 2*sig_width + self.MARGIN, y - 12, "Received By")
        
        # Footer
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.Color(0.5, 0.5, 0.5))
        c.drawCentredString(width/2, 30, f"Generated by UnidBox Order Copilot | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.drawCentredString(width/2, 20, "This is a computer-generated document. No signature required.")
        
        c.save()
        buffer.seek(0)
        return buffer.read()
    
    def _generate_html_pdf(self, do: DeliveryOrder) -> bytes:
        """Generate PDF from HTML (fallback method)"""
        from .do_templates import DOTemplates
        
        html = DOTemplates.delivery_order_html(do)
        
        # Try weasyprint
        try:
            from weasyprint import HTML
            buffer = io.BytesIO()
            HTML(string=html).write_pdf(buffer)
            buffer.seek(0)
            return buffer.read()
        except ImportError:
            pass
        
        # Try xhtml2pdf
        try:
            from xhtml2pdf import pisa
            buffer = io.BytesIO()
            pisa.CreatePDF(html, dest=buffer)
            buffer.seek(0)
            return buffer.read()
        except ImportError:
            pass
        
        # Return HTML as fallback
        return html.encode('utf-8')
    
    def save_to_file(self, do: DeliveryOrder, filepath: str) -> str:
        """
        Generate and save PDF to file.
        
        Args:
            do: DeliveryOrder object
            filepath: Path to save the PDF
            
        Returns:
            Path to the saved file
        """
        pdf_content = self.generate(do)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_content)
        
        return filepath
