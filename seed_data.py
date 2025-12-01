"""
Seed Data Script
Populates database with initial product data
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import DatabaseManager


def seed_database():
    """Populate database with initial data"""
    db = DatabaseManager('elevator_bot.db')
    
    print("Starting database seeding...")
    
    # Company settings
    print("\n1. Setting up company information...")
    db.set_setting('COMPANY_NAME', 'شرکت آسانسور روان رو دماوند')
    db.set_setting('COMPANY_ADDRESS', 'تهران - دماوند')
    db.set_setting('COMPANY_PHONE', '021-12345678')
    
    # Common products (used in both systems)
    print("\n2. Adding common products...")
    
    # Wires and cables
    db.add_product(
        code='WIRE-001',
        name='سیم کابل نمره 4 یا 0.75',
        unit='متر',
        price=50000,
        system='common',
        type='linear',
        factor=20,
        base_add=0,
        category='wire'
    )
    
    db.add_product(
        code='WIRE-002',
        name='تراول کابل',
        unit='متر',
        price=80000,
        system='common',
        type='linear',
        factor=4,
        base_add=5,
        category='wire'
    )
    
    db.add_product(
        code='WIRE-003',
        name='داکت نمره 3 یا 4',
        unit='متر',
        price=30000,
        system='common',
        type='linear',
        factor=4,
        base_add=0,
        category='wire'
    )
    
    db.add_product(
        code='WIRE-004',
        name='سیم تلفن',
        unit='متر',
        price=15000,
        system='common',
        type='linear',
        factor=5,
        base_add=0,
        category='wire'
    )
    
    # Door components
    db.add_product(
        code='DOOR-001',
        name='قفل درب',
        unit='عدد',
        price=350000,
        system='common',
        type='linear',
        factor=1,
        base_add=0,
        category='door'
    )
    
    db.add_product(
        code='DOOR-002',
        name='دیکتاتور (آرام‌بند)',
        unit='عدد',
        price=500000,
        system='common',
        type='linear',
        factor=1,
        base_add=0,
        category='door'
    )
    
    # Control and sensors
    db.add_product(
        code='CTRL-001',
        name='شاسی (کلید) طبقات',
        unit='عدد',
        price=450000,
        system='common',
        type='linear',
        factor=1,
        base_add=0,
        category='control'
    )
    
    db.add_product(
        code='SENS-001',
        name='آهنربا/سنسور (شابلون)',
        unit='عدد',
        price=200000,
        system='common',
        type='linear',
        factor=1,
        base_add=2,
        category='sensor'
    )
    
    # Cabin components
    db.add_product(
        code='CABIN-001',
        name='شاسی داخل کابین',
        unit='عدد',
        price=800000,
        system='common',
        type='dynamic_name',
        factor=1,
        base_add=0,
        name_pattern='شاسی داخل کابین ${stops} توقف',
        stops_offset=1,
        category='cabin'
    )
    
    db.add_product(
        code='CABIN-002',
        name='کابین آسانسور',
        unit='دستگاه',
        price=15000000,
        system='common',
        type='fixed',
        factor=1,
        base_add=0,
        category='cabin'
    )
    
    db.add_product(
        code='CTRL-002',
        name='تابلو فرمان',
        unit='دستگاه',
        price=8000000,
        system='common',
        type='fixed',
        factor=1,
        base_add=0,
        category='control'
    )
    
    # Labor
    db.add_product(
        code='LABOR-001',
        name='اجرت نصب',
        unit='واحد',
        price=5000000,
        system='common',
        type='linear',
        factor=1,
        base_add=0,
        category='labor'
    )
    
    # Hydraulic system products
    print("\n3. Adding hydraulic system products...")
    
    db.add_product(
        code='HYD-001',
        name='پاور یونیت هیدرولیک',
        unit='دستگاه',
        price=25000000,
        system='hydraulic',
        type='fixed',
        factor=1,
        base_add=0,
        category='motor'
    )
    
    db.add_product(
        code='HYD-002',
        name='جک هیدرولیک',
        unit='دستگاه',
        price=12000000,
        system='hydraulic',
        type='fixed',
        factor=1,
        base_add=0,
        category='motor'
    )
    
    db.add_product(
        code='HYD-003',
        name='روغن هیدرولیک',
        unit='لیتر',
        price=150000,
        system='hydraulic',
        type='fixed',
        factor=80,
        base_add=0,
        category='fluid'
    )
    
    db.add_product(
        code='HYD-004',
        name='شیلنگ فشار قوی',
        unit='متر',
        price=500000,
        system='hydraulic',
        type='linear',
        factor=2,
        base_add=3,
        category='hydraulic'
    )
    
    # Gearless system products
    print("\n4. Adding gearless system products...")
    
    db.add_product(
        code='GRL-001',
        name='موتور گیرلس',
        unit='دستگاه',
        price=35000000,
        system='gearless',
        type='fixed',
        factor=1,
        base_add=0,
        category='motor'
    )
    
    db.add_product(
        code='GRL-002',
        name='کادر وزنه تعادل',
        unit='دستگاه',
        price=5000000,
        system='gearless',
        type='fixed',
        factor=1,
        base_add=0,
        category='frame'
    )
    
    db.add_product(
        code='GRL-003',
        name='گاورنر (تنظیم‌کننده سرعت)',
        unit='دستگاه',
        price=6000000,
        system='gearless',
        type='fixed',
        factor=1,
        base_add=0,
        category='control'
    )
    
    db.add_product(
        code='GRL-004',
        name='سیم بکسل نمره 10',
        unit='متر',
        price=200000,
        system='gearless',
        type='linear',
        factor=10,
        base_add=0,
        category='wire'
    )
    
    db.add_product(
        code='GRL-005',
        name='سیم بکسل نمره 6',
        unit='متر',
        price=120000,
        system='gearless',
        type='linear',
        factor=8,
        base_add=0,
        category='wire'
    )
    
    db.add_product(
        code='GRL-006',
        name='سیم بکسل گاورنر',
        unit='متر',
        price=150000,
        system='gearless',
        type='linear',
        factor=10,
        base_add=0,
        category='wire'
    )
    
    db.add_product(
        code='GRL-007',
        name='ریل راهنما',
        unit='متر',
        price=800000,
        system='gearless',
        type='linear',
        factor=4,
        base_add=5,
        category='rail'
    )
    
    print("\n✅ Database seeding completed successfully!")
    print(f"Total products added: {len(db.get_products())}")
    
    # Show summary
    print("\n📊 Summary by system:")
    common_count = len(db.get_products(system_type='common'))
    hydraulic_count = len([p for p in db.get_products() if p['system'] == 'hydraulic'])
    gearless_count = len([p for p in db.get_products() if p['system'] == 'gearless'])
    
    print(f"  - Common products: {common_count}")
    print(f"  - Hydraulic products: {hydraulic_count}")
    print(f"  - Gearless products: {gearless_count}")


if __name__ == '__main__':
    seed_database()
