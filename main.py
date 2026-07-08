import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime
import random
import httpx

# دریافت اطلاعات حساس از تنظیمات رندر
TOKEN = os.getenv("TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

# مراحل گفتگو
ASKING_SHABA, ASKING_AMOUNT, ASKING_OWNER, ASKING_RECEIVER = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['ساخت رسید 📥']]
    await update.message.reply_text('🖐 سلام! ربات رسیدساز آماده است.', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ConversationHandler.END

async def ask_shaba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('⭕️ شماره شبا مقصد را وارد کنید:')
    return ASKING_SHABA

async def receive_shaba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shaba'] = update.message.text
    await update.message.reply_text('✅ دریافت شد. مبلغ را به تومان وارد کنید:')
    return ASKING_AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = update.message.text
    await update.message.reply_text('✅ دریافت شد. نام دارنده مبدا را وارد کنید:')
    return ASKING_OWNER

async def receive_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['owner'] = update.message.text
    await update.message.reply_text('✅ دریافت شد. نام دارنده مقصد را وارد کنید:')
    return ASKING_RECEIVER

async def receive_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['receiver'] = update.message.text
    await update.message.reply_text("⏳ در حال ساخت رسید...")

    template_path = "assets/template.jpg"
    font_path = "assets/font.ttf"
    result_path = "assets/result.jpg"

    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, 35)

    def draw_persian(text, pos):
        reshaped = arabic_reshaper.reshape(str(text))
        bidi = get_display(reshaped)
        draw.text(pos, bidi, fill="black", font=font)

    draw_persian(context.user_data['owner'], (350, 350))
    draw_persian(context.user_data['receiver'], (350, 400))
    draw_persian(context.user_data['shaba'], (350, 450))
    draw_persian(context.user_data['amount'], (350, 500))

    now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
    draw_persian(now, (350, 600))
    draw_persian(str(random.randint(10000000000000000000, 99999999999999999999)), (350, 750))

    img.save(result_path)
    await update.message.reply_photo(photo=open(result_path, 'rb'), caption="✅ رسید نهایی آماده شد.")
    return ConversationHandler.END

if __name__ == '__main__':
    # استفاده از متغیرها
    app = ApplicationBuilder().token(TOKEN).request(
        httpx.AsyncClient(proxy=PROXY_URL, timeout=30)
    ).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('ساخت رسید 📥'), ask_shaba)],
        states={
            ASKING_SHABA: [MessageHandler(filters.TEXT & (~filters.COMMAND), receive_shaba)],
            ASKING_AMOUNT: [MessageHandler(filters.TEXT & (~filters.COMMAND), receive_amount)],
            ASKING_OWNER: [MessageHandler(filters.TEXT & (~filters.COMMAND), receive_owner)],
            ASKING_RECEIVER: [MessageHandler(filters.TEXT & (~filters.COMMAND), receive_receiver)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)
    print("ربات با موفقیت استارت شد...")
    app.run_polling()
