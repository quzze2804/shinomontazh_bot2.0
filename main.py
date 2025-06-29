import os
import logging
from datetime import datetime, timedelta
from typing import Dict

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    ConversationHandler, 
    filters
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()
engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///appointments.db'))
Session = sessionmaker(bind=engine)

class Appointment(Base):
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    phone = Column(String)
    date_time = Column(DateTime)

Base.metadata.create_all(engine)

# Conversation states
NAME, PHONE, DATE, CONFIRM = range(4)

class TireServiceBot:
    def __init__(self):
        self.bot_token = "7939973394:AAHiqYYc5MSsiad1qslZ5rvgSnEEP7XeBfs"
        self.admin_chat_id = "7285220061"

    def generate_time_slots(self):
        """Generate available time slots from 8 AM to 5 PM with 30-minute intervals."""
        slots = []
        start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        end_time = start_time.replace(hour=17)
        
        while start_time <= end_time:
            slots.append(start_time.strftime("%H:%M"))
            start_time += timedelta(minutes=30)
        
        return slots

    async def start(self, update: Update, context):
        """Handle the /start command."""
        await update.message.reply_text(
            "Привет! Я бот для записи в шиномонтаж. Давайте запишем вас."
        )
        return await self.ask_name(update, context)

    async def ask_name(self, update: Update, context):
        """Ask for customer's name."""
        await update.message.reply_text("Пожалуйста, введите ваше имя:")
        return NAME

    async def save_name(self, update: Update, context):
        """Save customer's name and ask for phone number."""
        context.user_data['name'] = update.message.text
        await update.message.reply_text("Введите ваш номер телефона:")
        return PHONE

    async def save_phone(self, update: Update, context):
        """Save phone number and show available dates."""
        context.user_data['phone'] = update.message.text
        
        # Generate date buttons for next 7 days
        dates = [(datetime.now() + timedelta(days=i)).strftime("%d.%m.%Y") 
                 for i in range(7)]
        
        keyboard = [[KeyboardButton(date)] for date in dates]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            "Выберите дату:", 
            reply_markup=reply_markup
        )
        return DATE

    async def save_date(self, update: Update, context):
        """Save selected date and show time slots."""
        context.user_data['date'] = update.message.text
        
        # Generate time slots
        time_slots = self.generate_time_slots()
        keyboard = [[KeyboardButton(slot)] for slot in time_slots]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            "Выберите время:", 
            reply_markup=reply_markup
        )
        return CONFIRM

    async def confirm_appointment(self, update: Update, context):
        """Confirm appointment and save to database."""
        context.user_data['time'] = update.message.text
        full_datetime = datetime.strptime(
            f"{context.user_data['date']} {context.user_data['time']}", 
            "%d.%m.%Y %H:%M"
        )
        
        # Create appointment
        session = Session()
        try:
            new_appointment = Appointment(
                user_id=update.effective_user.id,
                name=context.user_data['name'],
                phone=context.user_data['phone'],
                date_time=full_datetime
            )
            session.add(new_appointment)
            session.commit()
            
            # Send confirmation to admin
            admin_message = (
                f"Новая запись:\n"
                f"Имя: {context.user_data['name']}\n"
                f"Телефон: {context.user_data['phone']}\n"
                f"Дата и время: {full_datetime.strftime('%d.%m.%Y %H:%M')}"
            )
            
            await context.bot.send_message(
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
  
