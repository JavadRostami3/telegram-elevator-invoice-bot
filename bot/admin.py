"""
Admin Panel for Bot
Allows admins to manage products and prices
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
import config

# Admin conversation states
ADMIN_MENU, EDIT_PRICE_SELECT, EDIT_PRICE_VALUE = range(3)


class AdminHandlers:
    """Handles admin panel operations"""
    
    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db = db_manager
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return str(user_id) in config.ADMIN_CHAT_IDS
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Admin panel entry point"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("⛔ شما دسترسی به پنل مدیریت ندارید.")
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("📋 مشاهده لیست محصولات", callback_data='view_products')],
            [InlineKeyboardButton("💰 ویرایش قیمت محصول", callback_data='edit_price')],
            [InlineKeyboardButton("⚙️ تنظیمات شرکت", callback_data='settings')],
            [InlineKeyboardButton("❌ خروج", callback_data='exit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔐 پنل مدیریت\n\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=reply_markup
        )
        return ADMIN_MENU
    
    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin menu selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'view_products':
            return await self.view_products(update, context)
        
        elif query.data == 'edit_price':
            return await self.edit_price_start(update, context)
        
        elif query.data == 'settings':
            await query.edit_message_text(
                "⚙️ تنظیمات شرکت\n\n"
                "این بخش در نسخه بعدی اضافه خواهد شد.\n"
                "برای بازگشت از /admin استفاده کنید."
            )
            return ConversationHandler.END
        
        elif query.data == 'exit':
            await query.edit_message_text("👋 از پنل مدیریت خارج شدید.")
            return ConversationHandler.END
    
    async def view_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """View all products"""
        query = update.callback_query
        
        products = self.db.get_products(is_active=1)
        
        if not products:
            await query.edit_message_text(
                "هیچ محصولی یافت نشد.\n"
                "برای بازگشت از /admin استفاده کنید."
            )
            return ConversationHandler.END
        
        # Format products list
        text = "📋 لیست محصولات:\n\n"
        for p in products[:20]:  # Limit to 20 for message length
            text += (
                f"🔹 ID: {p['id']}\n"
                f"نام: {p['name']}\n"
                f"قیمت: {p['price']:,} ریال\n"
                f"سیستم: {p['system']}\n"
                f"نوع: {p['type']}\n"
                "➖➖➖➖➖➖➖\n"
            )
        
        if len(products) > 20:
            text += f"\n... و {len(products) - 20} محصول دیگر"
        
        text += "\n\nبرای بازگشت از /admin استفاده کنید."
        
        await query.edit_message_text(text)
        return ConversationHandler.END
    
    async def edit_price_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start price editing process"""
        query = update.callback_query
        
        await query.edit_message_text(
            "💰 ویرایش قیمت محصول\n\n"
            "لطفاً ID محصول مورد نظر را وارد کنید:\n"
            "(برای مشاهده لیست محصولات از /admin > مشاهده لیست استفاده کنید)\n\n"
            "برای لغو: /cancel"
        )
        return EDIT_PRICE_SELECT
    
    async def edit_price_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive product ID for price edit"""
        try:
            product_id = int(update.message.text)
        except ValueError:
            await update.message.reply_text(
                "لطفاً یک عدد معتبر وارد کنید.\n"
                "برای لغو: /cancel"
            )
            return EDIT_PRICE_SELECT
        
        product = self.db.get_product_by_id(product_id)
        
        if not product:
            await update.message.reply_text(
                f"محصول با ID {product_id} یافت نشد.\n"
                "لطفاً دوباره تلاش کنید یا /cancel را بزنید."
            )
            return EDIT_PRICE_SELECT
        
        context.user_data['edit_product'] = product
        
        await update.message.reply_text(
            f"محصول انتخاب شده:\n\n"
            f"🔹 نام: {product['name']}\n"
            f"💰 قیمت فعلی: {product['price']:,} ریال\n\n"
            f"لطفاً قیمت جدید را به ریال وارد کنید:\n"
            "(فقط عدد، بدون کاما یا نقطه)\n\n"
            "برای لغو: /cancel"
        )
        return EDIT_PRICE_VALUE
    
    async def edit_price_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive new price and update"""
        try:
            new_price = int(update.message.text.replace(',', '').replace(' ', ''))
        except ValueError:
            await update.message.reply_text(
                "لطفاً یک عدد معتبر وارد کنید.\n"
                "برای لغو: /cancel"
            )
            return EDIT_PRICE_VALUE
        
        if new_price < 0:
            await update.message.reply_text(
                "قیمت نمی‌تواند منفی باشد.\n"
                "لطفاً دوباره وارد کنید یا /cancel بزنید."
            )
            return EDIT_PRICE_VALUE
        
        product = context.user_data['edit_product']
        
        # Update price
        success = self.db.update_product_price(product['id'], new_price)
        
        if success:
            await update.message.reply_text(
                f"✅ قیمت محصول با موفقیت بروزرسانی شد:\n\n"
                f"🔹 نام: {product['name']}\n"
                f"💰 قیمت قبلی: {product['price']:,} ریال\n"
                f"💰 قیمت جدید: {new_price:,} ریال\n\n"
                "برای ویرایش محصول دیگر از /admin استفاده کنید."
            )
        else:
            await update.message.reply_text(
                "❌ خطا در بروزرسانی قیمت.\n"
                "لطفاً دوباره تلاش کنید."
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def admin_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel admin operation"""
        await update.message.reply_text(
            "عملیات لغو شد.\n"
            "برای بازگشت به پنل مدیریت از /admin استفاده کنید."
        )
        context.user_data.clear()
        return ConversationHandler.END


def setup_admin_handlers(application, db_manager):
    """Setup admin handlers"""
    admin = AdminHandlers(db_manager)
    
    # Admin conversation handler
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin.admin_command)],
        states={
            ADMIN_MENU: [CallbackQueryHandler(admin.admin_menu)],
            EDIT_PRICE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.edit_price_select)],
            EDIT_PRICE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.edit_price_value)],
        },
        fallbacks=[CommandHandler('cancel', admin.admin_cancel)],
    )
    
    application.add_handler(admin_conv_handler)
