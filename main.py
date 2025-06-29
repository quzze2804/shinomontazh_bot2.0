```python
import os
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
SELECTING_DATE, SELECTING_TIME = range(2)

# Notification chat ID
NOTIFICATION_CHAT_ID = 7285220061

class TireServiceBot:
    def __init__(self, token):
        self.token = token
        self.appointments = {}

    async def start(self, update: Update, context):
        """Start the bot and show initial menu"""
        keyboard = [
            ['Записаться', 'Мои записи'],
            ['Отменить запись']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Привет! Я бот для записи на шиномонтаж. Что вы хотите сделать?', 
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    async def schedule_appointment(self, update: Update, context):
        """Start appointment scheduling process"""
        # Generate available dates (next 7 days)
        dates = [
            (datetime.now() + timedelta(days=i)).strftime('%d.%m.%Y') 
            for i in range(7)
        ]
        
        keyboard = [dates[i:i+3] for i in range(0, len(dates), 3)]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            'Выберите дату для записи:', 
            reply_markup=reply_markup
        )
        return SELECTING_DATE

    async def select_time(self, update: Update, context):
        """Select available time slots"""
        selected_date = update.message.text
        context.user_data['selected_date'] = selected_date

        # Generate time slots from 8:00 to 17:00 with 30-minute intervals
        time_slots = [
            f'{hour:02d}:{minute:02d}' 
            for hour in range(8, 18) 
            for minute in [0, 30]
        ]

        keyboard = [time_slots[i:i+3] for i in range(0, len(time_slots), 3)]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            'Выберите время:', 
            reply_markup=reply_markup
        )
        return SELECTING_TIME

    async def confirm_appointment(self, update: Update, context):
        """Confirm the appointment"""
        selected_time = update.message.text
        selected_date = context.user_data['selected_date']
        user = update.effective_user

        # Store appointment
        appointment_key = f"{selected_date} {selected_time}"
        self.appointments[appointment_key] = {
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name
        }

        # Send notification to admin
        await context.bot.send_message(
            chat_id=NOTIFICATION_CHAT_ID, 
            text=f"Новая запись:\n"
                 f"Дата: {selected_date}\n"
                 f"Время: {selected_time}\n"
                 f"Пользователь: {user.full_name} (@{user.username})"
        )

        await update.message.reply_text(
            f'Вы записаны на {selected_date} в {selected_time}. '
            'Ждем вас в нашем шиномонтаже!', 
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    def run(self):
        """Run the bot"""
        application = Application.builder().token(self.token).build()

        # Conversation handler for appointment scheduling
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^Записаться$'), self.schedule_appointment)
            ],
            states={
                SELECTING_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_time)
                ],
                SELECTING_TIME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_appointment)
                ]
            },
            fallbacks=[CommandHandler('start', self.start)]
        )

        # Add handlers
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('start', self.start))

        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    bot = TireServiceBot(os.getenv('BOT_TOKEN'))
    bot.run()

if __name__ == '__main__':
    main()
```
  
                chat_id=self.admin_chat_id, 
                text=admin_message
            )
            
            await update.message.reply_text(
                "Спасибо! Ваша запись подтверждена. Мы с вами свяжемся."
            )
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при сохранении записи."
            )
        finally:
            session.close()
        
        return ConversationHandler.END

    def main(self):
        """Start the bot."""
        application = Application.builder().token(self.bot_token).build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_name)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_phone)],
                DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_date)],
                CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_appointment)]
            },
            fallbacks=[CommandHandler('cancel', lambda update, context: ConversationHandler.END)]
        )
        
        application.add_handler(conv_handler)
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = TireServiceBot()
    bot.main()
