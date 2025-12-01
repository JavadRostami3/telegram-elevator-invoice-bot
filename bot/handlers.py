"""
Telegram Bot Handlers
Main conversation flow for invoice creation
"""
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import DatabaseManager
from logic import InvoiceCalculator
from pdf import PDFGenerator
import config

# Conversation states
CUSTOMER_NAME, PROJECT_NAME, SYSTEM_TYPE, FLOORS, CONFIRMATION = range(5)


class BotHandlers:
    """Handles all bot conversation and commands"""
    
    def __init__(self):
        """Initialize handlers with database and logic modules"""
        self.db = DatabaseManager(config.DATABASE_PATH)
        self.calculator = InvoiceCalculator(self.db)
        self.pdf_generator = PDFGenerator(
            template_dir='templates',
            output_dir=config.OUTPUT_DIR,
            wkhtmltopdf_path=config.WKHTMLTOPDF_PATH
        )
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start command - Begin invoice creation process"""
        await update.message.reply_text(
            "سلام! به ربات صدور پیش‌فاکتور آسانسور خوش آمدید.\n\n"
            "لطفاً نام مشتری را وارد کنید:"
        )
        return CUSTOMER_NAME
    
    async def customer_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive customer name"""
        context.user_data['customer_name'] = update.message.text
        
        await update.message.reply_text(
            f"نام مشتری: {update.message.text}\n\n"
            "حالا لطفاً نام پروژه یا موقعیت را وارد کنید:"
        )
        return PROJECT_NAME
    
    async def project_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive project name"""
        context.user_data['project_name'] = update.message.text
        
        # Show system type keyboard
        keyboard = [
            ['هیدرولیک', 'کششی گیرلس']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"نام پروژه: {update.message.text}\n\n"
            "لطفاً نوع سیستم آسانسور را انتخاب کنید:",
            reply_markup=reply_markup
        )
        return SYSTEM_TYPE
    
    async def system_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive system type"""
        system_text = update.message.text
        
        # Map Persian to English
        system_map = {
            'هیدرولیک': 'hydraulic',
            'کششی گیرلس': 'gearless'
        }
        
        if system_text not in system_map:
            await update.message.reply_text(
                "لطفاً یکی از دکمه‌های نوع سیستم را انتخاب کنید:"
            )
            return SYSTEM_TYPE
        
        context.user_data['system_type'] = system_map[system_text]
        context.user_data['system_text'] = system_text
        
        await update.message.reply_text(
            f"نوع سیستم: {system_text}\n\n"
            "حالا تعداد توقف (طبقات) را به عدد وارد کنید:\n"
            "(مثال: 5)",
            reply_markup=ReplyKeyboardRemove()
        )
        return FLOORS
    
    async def floors(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive number of floors"""
        try:
            floors = int(update.message.text)
        except ValueError:
            await update.message.reply_text(
                "لطفاً تعداد توقف را به عدد وارد کنید (مثال: 5):"
            )
            return FLOORS
        
        # Validate floors
        is_valid, error_msg = self.calculator.validate_floors(floors)
        if not is_valid:
            await update.message.reply_text(f"{error_msg}\n\nلطفاً دوباره وارد کنید:")
            return FLOORS
        
        context.user_data['floors'] = floors
        
        # Calculate invoice
        try:
            result = self.calculator.calculate_invoice(
                floors=floors,
                system_type=context.user_data['system_type']
            )
            context.user_data['calculation_result'] = result
            
            # Show confirmation
            confirmation_text = (
                "✅ اطلاعات پیش‌فاکتور:\n\n"
                f"👤 مشتری: {context.user_data['customer_name']}\n"
                f"📍 پروژه: {context.user_data['project_name']}\n"
                f"🔧 نوع سیستم: {context.user_data['system_text']}\n"
                f"🏢 تعداد توقف: {floors}\n"
                f"💰 جمع کل: {self.calculator.format_price(result['total_price'])} ریال\n"
                f"📦 تعداد اقلام: {len(result['items'])}\n\n"
                "آیا اطلاعات صحیح است؟\n"
                "برای صدور PDF عدد 1 و برای انصراف عدد 0 را ارسال کنید:"
            )
            
            await update.message.reply_text(confirmation_text)
            return CONFIRMATION
            
        except Exception as e:
            await update.message.reply_text(
                f"خطا در محاسبه فاکتور: {str(e)}\n\n"
                "لطفاً دوباره تلاش کنید یا با /cancel لغو کنید."
            )
            return FLOORS
    
    async def confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle confirmation and generate PDF"""
        response = update.message.text.strip()
        
        if response == '0':
            await update.message.reply_text(
                "عملیات لغو شد.\n"
                "برای شروع مجدد از دستور /start استفاده کنید."
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        if response != '1':
            await update.message.reply_text(
                "لطفاً برای تایید عدد 1 و برای انصراف عدد 0 را ارسال کنید:"
            )
            return CONFIRMATION
        
        # Generate invoice
        await update.message.reply_text("در حال تولید PDF... لطفاً صبر کنید...")
        
        try:
            result = context.user_data['calculation_result']
            
            # Save to database
            invoice_id = self.db.create_invoice(
                customer_name=context.user_data['customer_name'],
                project_name=context.user_data['project_name'],
                system=context.user_data['system_type'],
                floors=context.user_data['floors'],
                total_price=result['total_price']
            )
            
            # Save invoice items
            for item in result['items']:
                self.db.add_invoice_item(
                    invoice_id=invoice_id,
                    product_id=item['product_id'],
                    name=item['name'],
                    unit=item['unit'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )
            
            # Get company info from settings
            company_info = {
                'name': self.db.get_setting('COMPANY_NAME', 'شرکت آسانسور روان رو دماوند'),
                'address': self.db.get_setting('COMPANY_ADDRESS', 'تهران - دماوند'),
                'phone': self.db.get_setting('COMPANY_PHONE', '021-12345678')
            }
            
            # Prepare invoice data for PDF
            invoice_data = {
                'id': invoice_id,
                'customer_name': context.user_data['customer_name'],
                'project_name': context.user_data['project_name'],
                'system': context.user_data['system_type'],
                'floors': context.user_data['floors'],
                'total_price': result['total_price']
            }
            
            # Generate PDF
            pdf_path = self.pdf_generator.generate_invoice(
                invoice_data=invoice_data,
                items=result['items'],
                company_info=company_info
            )
            
            # Send PDF to user
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename=os.path.basename(pdf_path),
                    caption=f"✅ پیش‌فاکتور شماره {invoice_id} با موفقیت صادر شد."
                )
            
            await update.message.reply_text(
                "برای صدور پیش‌فاکتور جدید از دستور /start استفاده کنید."
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"خطا در تولید فاکتور: {str(e)}\n\n"
                "لطفاً با پشتیبانی تماس بگیرید."
            )
            context.user_data.clear()
            return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation"""
        await update.message.reply_text(
            "عملیات لغو شد.\n"
            "برای شروع مجدد از دستور /start استفاده کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = (
            "🤖 راهنمای ربات صدور پیش‌فاکتور آسانسور\n\n"
            "دستورات:\n"
            "/start - شروع صدور پیش‌فاکتور جدید\n"
            "/cancel - لغو عملیات جاری\n"
            "/help - نمایش این راهنما\n"
            "/admin - ورود به پنل مدیریت (فقط ادمین)\n\n"
            "برای صدور پیش‌فاکتور:\n"
            "1️⃣ نام مشتری را وارد کنید\n"
            "2️⃣ نام پروژه را وارد کنید\n"
            "3️⃣ نوع سیستم را انتخاب کنید\n"
            "4️⃣ تعداد توقف را وارد کنید\n"
            "5️⃣ اطلاعات را تایید کنید\n"
            "6️⃣ فایل PDF دریافت کنید"
        )
        await update.message.reply_text(help_text)


def setup_handlers(application: Application) -> None:
    """Setup all handlers for the bot"""
    bot_handlers = BotHandlers()
    
    # Conversation handler for invoice creation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', bot_handlers.start)],
        states={
            CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.customer_name)],
            PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.project_name)],
            SYSTEM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.system_type)],
            FLOORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.floors)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.confirmation)],
        },
        fallbacks=[CommandHandler('cancel', bot_handlers.cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', bot_handlers.help_command))
