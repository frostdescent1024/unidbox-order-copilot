"""
Delivery Order Templates Module for UnidBox Order Copilot

This module provides HTML templates for Delivery Order documents
that can be converted to PDF.
"""

from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .do_generator import DeliveryOrder


class DOTemplates:
    """
    HTML templates for Delivery Order documents.
    
    These templates are designed for PDF generation with proper
    page formatting and print-ready styling.
    """
    
    @classmethod
    def delivery_order_html(cls, do: 'DeliveryOrder') -> str:
        """Generate HTML for a Delivery Order"""
        
        # Build items rows
        items_html = ""
        for item in do.items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">{item.line_number}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{item.product_name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{item.description or '-'}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">{item.quantity} {item.unit}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">${item.unit_price:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">${item.total_price:.2f}</td>
            </tr>
            """
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Delivery Order - {do.do_number}</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 10pt;
            color: #1f2937;
            line-height: 1.4;
        }}
        
        .container {{
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background-color: #1e3a5f;
            color: white;
            padding: 20px;
            margin: -20px -20px 20px -20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header h1 {{
            font-size: 24pt;
            font-weight: bold;
        }}
        
        .header .company {{
            font-size: 10pt;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        .header .do-info {{
            text-align: right;
        }}
        
        .header .do-number {{
            font-size: 14pt;
            font-weight: bold;
        }}
        
        .addresses {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .address-box {{
            flex: 1;
            background-color: #f3f4f6;
            padding: 15px;
            border-radius: 4px;
        }}
        
        .address-box h3 {{
            font-size: 9pt;
            color: #6b7280;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        
        .address-box p {{
            margin: 3px 0;
        }}
        
        .order-details {{
            display: flex;
            gap: 30px;
            margin-bottom: 20px;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .order-details span {{
            color: #6b7280;
        }}
        
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        .items-table thead {{
            background-color: #1e3a5f;
            color: white;
        }}
        
        .items-table th {{
            padding: 12px 10px;
            text-align: left;
            font-weight: bold;
            font-size: 9pt;
        }}
        
        .items-table th:first-child {{
            text-align: center;
            width: 40px;
        }}
        
        .items-table th:nth-child(4),
        .items-table th:nth-child(5),
        .items-table th:nth-child(6) {{
            text-align: right;
        }}
        
        .items-table tbody tr:nth-child(even) {{
            background-color: #f9fafb;
        }}
        
        .totals {{
            width: 250px;
            margin-left: auto;
            margin-bottom: 30px;
        }}
        
        .totals table {{
            width: 100%;
        }}
        
        .totals td {{
            padding: 8px 0;
        }}
        
        .totals td:last-child {{
            text-align: right;
        }}
        
        .totals .total-row {{
            background-color: #1e3a5f;
            color: white;
            font-weight: bold;
            font-size: 12pt;
        }}
        
        .totals .total-row td {{
            padding: 12px 10px;
        }}
        
        .instructions {{
            background-color: #fef3c7;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #f59e0b;
            margin-bottom: 30px;
        }}
        
        .instructions h4 {{
            font-size: 9pt;
            color: #92400e;
            margin-bottom: 5px;
        }}
        
        .instructions p {{
            color: #92400e;
        }}
        
        .signatures {{
            display: flex;
            justify-content: space-between;
            margin-top: 50px;
            padding-top: 20px;
        }}
        
        .signature-box {{
            width: 30%;
            text-align: center;
        }}
        
        .signature-line {{
            border-top: 1px solid #1f2937;
            margin-bottom: 5px;
            padding-top: 40px;
        }}
        
        .signature-label {{
            font-size: 8pt;
            color: #6b7280;
        }}
        
        .footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 7pt;
            color: #9ca3af;
            padding: 10px;
            border-top: 1px solid #e5e7eb;
        }}
        
        @media print {{
            .container {{
                padding: 0;
            }}
            
            .header {{
                margin: 0 0 20px 0;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>DELIVERY ORDER</h1>
                <div class="company">UnidBox Hardware Pte. Ltd.</div>
            </div>
            <div class="do-info">
                <div class="do-number">DO#: {do.do_number}</div>
                <div>Date: {do.issue_date}</div>
            </div>
        </div>
        
        <div class="addresses">
            <div class="address-box">
                <h3>Ship From</h3>
                <p><strong>{do.ship_from.name}</strong></p>
                <p>{do.ship_from.address_line1}</p>
                {f'<p>{do.ship_from.address_line2}</p>' if do.ship_from.address_line2 else ''}
                <p>{do.ship_from.city} {do.ship_from.postal_code or ''}</p>
                {f'<p>Tel: {do.ship_from.phone}</p>' if do.ship_from.phone else ''}
            </div>
            <div class="address-box">
                <h3>Ship To</h3>
                <p><strong>{do.ship_to.name}</strong></p>
                <p>{do.ship_to.address_line1}</p>
                {f'<p>{do.ship_to.address_line2}</p>' if do.ship_to.address_line2 else ''}
                <p>{do.ship_to.city} {do.ship_to.postal_code or ''}</p>
                {f'<p>Tel: {do.ship_to.phone}</p>' if do.ship_to.phone else ''}
            </div>
        </div>
        
        <div class="order-details">
            <div><span>Order ID:</span> <strong>{do.order_id}</strong></div>
            <div><span>Delivery Date:</span> <strong>{do.delivery_date or 'TBD'}</strong></div>
            <div><span>Payment Terms:</span> <strong>{do.payment_terms}</strong></div>
        </div>
        
        <table class="items-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Product</th>
                    <th>Description</th>
                    <th style="text-align: center;">Qty</th>
                    <th style="text-align: right;">Unit Price</th>
                    <th style="text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <div class="totals">
            <table>
                <tr>
                    <td>Subtotal</td>
                    <td>${do.subtotal:.2f}</td>
                </tr>
                <tr>
                    <td>GST ({do.tax_rate*100:.0f}%)</td>
                    <td>${do.tax_amount:.2f}</td>
                </tr>
                <tr>
                    <td>Shipping</td>
                    <td>${do.shipping_cost:.2f}</td>
                </tr>
                <tr class="total-row">
                    <td>TOTAL</td>
                    <td>${do.total:.2f} {do.currency}</td>
                </tr>
            </table>
        </div>
        
        {f'''
        <div class="instructions">
            <h4>Special Instructions</h4>
            <p>{do.special_instructions}</p>
        </div>
        ''' if do.special_instructions else ''}
        
        <div class="signatures">
            <div class="signature-box">
                <div class="signature-line"></div>
                <div class="signature-label">Prepared By</div>
                {f'<div>{do.prepared_by}</div>' if do.prepared_by else ''}
            </div>
            <div class="signature-box">
                <div class="signature-line"></div>
                <div class="signature-label">Approved By</div>
            </div>
            <div class="signature-box">
                <div class="signature-line"></div>
                <div class="signature-label">Received By</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by UnidBox Order Copilot | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p>This is a computer-generated document. No signature required.</p>
        </div>
    </div>
</body>
</html>
"""
