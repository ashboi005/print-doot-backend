from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import inch
import json
import requests
from urllib.parse import urlparse
import os

def fetch_image(url):
    """Fetch an image from a URL and return it as a ReportLab Image object."""
    try:
        # Check if URL is valid
        if not url or not urlparse(url).scheme:
            return None

        response = requests.get(url, stream=True, timeout=5)
        if response.status_code == 200:
            img_data = BytesIO(response.content)
            img = Image(img_data, width=1.5*inch, height=1.5*inch)
            return img
        return None
    except Exception:
        return None

def format_datetime(dt):
    """Format datetime for display."""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_money(amount):
    """Format money amount."""
    if amount is None:
        return "₹0"
    return f"₹{amount/100:.2f}" if amount >= 100 else f"₹{amount}"

def create_orders_pdf(orders, customer_details, products, buffer=None):
    """
    Generate a PDF report with order details
    
    Args:
        orders: List of order objects with their items
        customer_details: Dict of customer details by clerkId
        products: Dict of product details by product_id
        buffer: BytesIO buffer (optional, creates new one if not provided)
        
    Returns:
        BytesIO buffer with the PDF
    """
    if buffer is None:
        buffer = BytesIO()
    
    # Create the PDF document with specific settings for AWS Lambda compatibility
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="PrintDoot Orders Report",
        author="PrintDoot System",
        subject="Order Report",
        creator="PrintDoot"
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=12
    )
    
    report_title = "PrintDoot Orders Report"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"{report_title}", title_style))
    elements.append(Paragraph(f"Generated: {date_str}", styles["Normal"]))
    elements.append(Spacer(1, 0.25*inch))
    
    # For each order, create a section
    for order in orders:
        # Add order header
        elements.append(Paragraph(f"Order ID: {order.order_id}", styles["Heading2"]))
        elements.append(Paragraph(f"Date: {format_datetime(order.created_at)}", styles["Normal"]))
        elements.append(Paragraph(f"Status: {order.status}", styles["Normal"]))
        
        # Add customer details
        customer = customer_details.get(order.clerkId)
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Customer Details:", styles["Heading3"]))
        
        if customer:
            customer_data = [
                ["Name", f"{customer['first_name']} {customer['last_name']}"],
                ["Email", customer["email"]],
                ["Phone", customer["phone_number"]],
            ]
            
            # Add address details if available
            if customer.get('details'):
                address_parts = []
                if customer['details'].get('address'):
                    address_parts.append(customer['details']['address'])
                if customer['details'].get('city'):
                    address_parts.append(customer['details']['city'])
                if customer['details'].get('state'):
                    address_parts.append(customer['details']['state'])
                if customer['details'].get('country'):
                    address_parts.append(customer['details']['country'])
                if customer['details'].get('pin_code'):
                    address_parts.append(customer['details']['pin_code'])
                
                if address_parts:
                    customer_data.append(["Address", ", ".join(address_parts)])
        else:
            customer_data = [["Customer ID", order.clerkId]]
            
        # Create customer table
        customer_table = Table(customer_data, colWidths=[1.5*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        elements.append(customer_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Add order items
        elements.append(Paragraph("Order Items:", styles["Heading3"]))
        
        # Table header
        item_data = [["Item", "Details", "Qty", "Price", "Subtotal"]]
        
        # Add items
        if order.items:
            total = 0
            for item in order.items:
                product = products.get(item.product_id, {})
                product_name = product.get('name', item.product_id)
                
                # Prepare details text
                details = []
                if item.selected_customizations:
                    for k, v in item.selected_customizations.items():
                        details.append(f"{k}: {v}")
                
                if item.user_customization_type:
                    details.append(f"Custom {item.user_customization_type}")
                    
                details_text = "\n".join(details) if details else ""
                
                # Calculate subtotal
                subtotal = item.individual_price * item.quantity
                total += subtotal
                
                # Add to table data
                item_data.append([
                    product_name, 
                    details_text,
                    str(item.quantity), 
                    format_money(item.individual_price), 
                    format_money(subtotal)
                ])
            
            # Add total row
            item_data.append(["", "", "", "Total:", format_money(total)])
            
            # Create items table
            col_widths = [2*inch, 2*inch, 0.5*inch, 1*inch, 1*inch]
            items_table = Table(item_data, colWidths=col_widths)
            
            items_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('FONTWEIGHT', (0, 0), (-1, 0), 'BOLD'),
                ('FONTWEIGHT', (-2, -1), (-1, -1), 'BOLD'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(items_table)
        else:
            elements.append(Paragraph("No items in this order.", styles["Normal"]))
        
        # Add spacer and page break for next order
        elements.append(Spacer(1, 0.5*inch))
        elements.append(PageBreak())
    
    # Build the PDF with proper compression settings for AWS Lambda
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_order_pdf_from_db_data(orders, users, user_details, products):
    """
    Create a PDF from database objects
    
    Args:
        orders: List of Order objects from the database
        users: Dict of User objects by clerkId
        user_details: Dict of UserDetails objects by clerkId
        products: Dict of Product objects by product_id
        
    Returns:
        BytesIO buffer with the PDF
    """
    # Process users and user details into a combined dict
    customer_details = {}
    for clerk_id, user in users.items():
        customer_details[clerk_id] = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number
        }
        
        if clerk_id in user_details:
            customer_details[clerk_id]['details'] = {
                'address': user_details[clerk_id].address,
                'city': user_details[clerk_id].city,
                'state': user_details[clerk_id].state,
                'country': user_details[clerk_id].country,
                'pin_code': user_details[clerk_id].pin_code
            }
    
    # Process products data
    product_details = {}
    for prod_id, product in products.items():
        product_details[prod_id] = {
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'main_image_url': product.main_image_url
        }
    
    return create_orders_pdf(orders, customer_details, product_details) 