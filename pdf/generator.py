"""
PDF Generator Module
Generates professional PDF invoices using Jinja2 and pdfkit
"""
import os
from datetime import datetime
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
import pdfkit
from pathlib import Path


class PDFGenerator:
    """Generates PDF invoices from templates"""
    
    def __init__(self, template_dir: str = "templates", output_dir: str = "output",
                 wkhtmltopdf_path: str = None):
        """
        Initialize PDF generator
        
        Args:
            template_dir: Directory containing Jinja2 templates
            output_dir: Directory for output PDF files
            wkhtmltopdf_path: Path to wkhtmltopdf executable
        """
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # Setup pdfkit configuration
        self.pdfkit_config = None
        if wkhtmltopdf_path and os.path.exists(wkhtmltopdf_path):
            self.pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    
    def generate_invoice(self, invoice_data: Dict, items: List[Dict],
                        company_info: Dict = None) -> str:
        """
        Generate PDF invoice
        
        Args:
            invoice_data: Invoice information (customer, project, system, floors, etc.)
            items: List of invoice items
            company_info: Company information for header
        
        Returns:
            Path to generated PDF file
        """
        # Load template
        template = self.env.get_template('invoice_template.html')
        
        # Prepare data for template
        context = self._prepare_context(invoice_data, items, company_info)
        
        # Render HTML
        html_content = template.render(context)
        
        # Generate filename
        filename = self._generate_filename(invoice_data)
        output_path = os.path.join(self.output_dir, filename)
        
        # PDF options for RTL and Persian support
        options = {
            'page-size': 'A4',
            'margin-top': '15mm',
            'margin-right': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '15mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        # Generate PDF
        try:
            if self.pdfkit_config:
                pdfkit.from_string(html_content, output_path, 
                                 options=options, configuration=self.pdfkit_config)
            else:
                pdfkit.from_string(html_content, output_path, options=options)
        except Exception as e:
            raise Exception(f"خطا در تولید PDF: {str(e)}")
        
        return output_path
    
    def _prepare_context(self, invoice_data: Dict, items: List[Dict],
                        company_info: Dict = None) -> Dict:
        """
        Prepare template context with all necessary data
        
        Args:
            invoice_data: Invoice data
            items: Invoice items
            company_info: Company information
        
        Returns:
            Context dictionary for template
        """
        # Default company info
        if company_info is None:
            company_info = {
                'name': 'شرکت آسانسور روان رو دماوند',
                'address': 'تهران - دماوند',
                'phone': '021-12345678',
                'logo_path': None
            }
        
        # Format date
        persian_date = self._format_persian_date(datetime.now())
        
        # System type in Persian
        system_persian = {
            'hydraulic': 'هیدرولیک',
            'gearless': 'کششی گیرلس'
        }.get(invoice_data.get('system', ''), invoice_data.get('system', ''))
        
        # Calculate totals
        total_price = invoice_data.get('total_price', 0)
        
        context = {
            'invoice': {
                'id': invoice_data.get('id', ''),
                'customer_name': invoice_data.get('customer_name', ''),
                'project_name': invoice_data.get('project_name', ''),
                'system': system_persian,
                'floors': invoice_data.get('floors', 0),
                'date': persian_date,
                'total_price': total_price,
                'total_price_formatted': self._format_number(total_price)
            },
            'company': company_info,
            'items': self._format_items(items)
        }
        
        return context
    
    def _format_items(self, items: List[Dict]) -> List[Dict]:
        """Format items for display in template"""
        formatted_items = []
        
        for idx, item in enumerate(items, start=1):
            formatted_item = {
                'row': idx,
                'name': item.get('name', ''),
                'unit': item.get('unit', ''),
                'quantity': self._format_number(item.get('quantity', 0)),
                'unit_price': self._format_number(item.get('unit_price', 0)),
                'total_price': self._format_number(item.get('total_price', 0))
            }
            formatted_items.append(formatted_item)
        
        return formatted_items
    
    def _format_number(self, number: float) -> str:
        """Format number with thousand separators"""
        if isinstance(number, float) and number.is_integer():
            number = int(number)
        return f"{number:,}"
    
    def _format_persian_date(self, date: datetime) -> str:
        """
        Format date in Persian (simplified version)
        For production, use persiantools or jdatetime library
        """
        # Simple format for now - can be enhanced with jdatetime
        return date.strftime('%Y/%m/%d')
    
    def _generate_filename(self, invoice_data: Dict) -> str:
        """Generate unique filename for PDF"""
        invoice_id = invoice_data.get('id', 'temp')
        customer = invoice_data.get('customer_name', 'customer').replace(' ', '_')
        project = invoice_data.get('project_name', 'project').replace(' ', '_')
        
        # Clean filename from special characters
        customer = ''.join(c for c in customer if c.isalnum() or c == '_')[:20]
        project = ''.join(c for c in project if c.isalnum() or c == '_')[:20]
        
        filename = f"invoice_{invoice_id}_{customer}_{project}.pdf"
        return filename
