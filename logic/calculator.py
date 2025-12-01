"""
Invoice Calculator Module
Handles all calculation logic for elevator invoices
"""
from typing import Dict, List
from string import Template


class InvoiceCalculator:
    """Calculates invoice items based on products and floors"""
    
    def __init__(self, db_manager):
        """
        Initialize calculator with database manager
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def calculate_invoice(self, floors: int, system_type: str) -> Dict:
        """
        Calculate invoice items for given floors and system type
        
        Args:
            floors: Number of floors/stops (N)
            system_type: 'hydraulic' or 'gearless'
        
        Returns:
            Dictionary with:
                - items: List of calculated items
                - total_price: Total invoice price
        """
        # Get applicable products
        products = self.db.get_products(
            system_type=system_type,
            is_active=1,
            floors=floors
        )
        
        items = []
        total_price = 0
        
        for product in products:
            # Calculate quantity based on product type
            quantity = self._calculate_quantity(product, floors)
            
            # Get final name (handle dynamic naming)
            final_name = self._get_final_name(product, floors)
            
            # Calculate item total price
            item_total = int(quantity * product['price'])
            
            item = {
                'product_id': product['id'],
                'name': final_name,
                'unit': product['unit'],
                'quantity': quantity,
                'unit_price': product['price'],
                'total_price': item_total
            }
            
            items.append(item)
            total_price += item_total
        
        return {
            'items': items,
            'total_price': total_price
        }
    
    def _calculate_quantity(self, product: Dict, floors: int) -> float:
        """
        Calculate quantity for a product based on its type
        
        Args:
            product: Product dictionary from database
            floors: Number of floors
        
        Returns:
            Calculated quantity
        """
        product_type = product['type']
        factor = product['factor'] or 0
        base_add = product['base_add'] or 0
        
        if product_type == 'fixed':
            # Fixed quantity (usually stored in factor or default to 1)
            return factor if factor > 0 else 1.0
        
        elif product_type == 'linear':
            # Linear calculation: quantity = factor * N + base_add
            return factor * floors + base_add
        
        elif product_type == 'dynamic_name':
            # Dynamic name items - quantity can be fixed or linear
            # Check if it uses linear calculation
            if factor > 0:
                return factor * floors + base_add
            else:
                # Default to 1 if no factor specified
                return 1.0
        
        else:
            # Default case
            return 1.0
    
    def _get_final_name(self, product: Dict, floors: int) -> str:
        """
        Get final name for product, handling dynamic naming
        
        Args:
            product: Product dictionary
            floors: Number of floors
        
        Returns:
            Final product name
        """
        if product['type'] == 'dynamic_name' and product['name_pattern']:
            # Use name pattern to generate dynamic name
            stops_offset = product['stops_offset'] or 0
            actual_stops = floors + stops_offset
            
            # Use string Template for safe substitution
            template = Template(product['name_pattern'])
            
            try:
                final_name = template.safe_substitute(
                    stops=actual_stops,
                    floors=floors,
                    N=floors
                )
                return final_name
            except Exception:
                # Fallback to base name if pattern fails
                return product['name']
        
        return product['name']
    
    def format_price(self, price: int) -> str:
        """
        Format price with thousand separators
        
        Args:
            price: Price in Rials
        
        Returns:
            Formatted price string
        """
        return f"{price:,}"
    
    def validate_floors(self, floors: int) -> tuple[bool, str]:
        """
        Validate floor count
        
        Args:
            floors: Number of floors to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(floors, int):
            return False, "تعداد توقف باید یک عدد صحیح باشد"
        
        if floors < 1:
            return False, "تعداد توقف باید حداقل ۱ باشد"
        
        if floors > 100:
            return False, "تعداد توقف نمی‌تواند بیش از ۱۰۰ باشد"
        
        return True, ""
    
    def validate_system_type(self, system_type: str) -> tuple[bool, str]:
        """
        Validate system type
        
        Args:
            system_type: System type to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_systems = ['hydraulic', 'gearless']
        
        if system_type not in valid_systems:
            return False, f"نوع سیستم باید یکی از {valid_systems} باشد"
        
        return True, ""
