
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import numpy as np

logging.basicConfig(level=logging.INFO)

# مراحل گفت‌وگو
ASK_MEMBERS, COLLECT_FEATURES = range(2)

user_data = {}

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! 🤖\nمن ربات تحلیل تیمی هستم. چند عضو توی تیم شما هست؟ (۲ تا ۱۰)")
    return ASK_MEMBERS

# گرفتن تعداد اعضا
async def ask_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = int(update.message.text)
        if not 2 <= n <= 10:
            raise ValueError
        context.user_data['n'] = n
        context.user_data['members'] = []
        context.user_data['step'] = 0
        await update.message.reply_text(f"خیلی خب، لطفاً ویژگی‌های عضو 1 رو به این صورت وارد کن:\n\nانگیزه، وظیفه‌شناسی، IQ\nمثلاً: 4.5, 3.2, 120")
        return COLLECT_FEATURES
    except:
        await update.message.reply_text("لطفاً فقط یک عدد بین ۲ تا ۱۰ بفرست 🙏")
        return ASK_MEMBERS

# گرفتن ویژگی‌ها
async def collect_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        values = list(map(float, update.message.text.strip().split(",")))
        if len(values) != 3:
            raise ValueError
        context.user_data['members'].append(values)
        context.user_data['step'] += 1

        if context.user_data['step'] == context.user_data['n']:
            return await finish_analysis(update, context)
        else:
            await update.message.reply_text(f"ویژگی‌های عضو {context.user_data['step'] + 1} رو وارد کن:\n(مثلاً 5.2, 3.8, 100)")
            return COLLECT_FEATURES
    except:
        await update.message.reply_text("اطلاعات نادرسته 😕 لطفاً سه عدد با کاما جدا شده وارد کن")
        return COLLECT_FEATURES

# پایان: محاسبه هم‌ترازی و عملکرد
async def finish_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = np.array(context.user_data['members'])

    def align_2d(col1, col2, r1, r2):
        v1, v2 = data[:, col1], data[:, col2]
        return np.mean([1 - abs(a - b) / ((r1 + r2)/2) for a, b in zip(v1, v2)])

    def align_3d():
        sims = []
        for i in range(len(data)):
            for j in range(i+1, len(data)):
                d = np.linalg.norm((data[i] - data[j]) / np.array([6, 4, 60]))
                sims.append(1 - d / np.sqrt(3))
        return np.mean(sims)

    a1 = align_2d(0, 1, 6, 4)
    a2 = align_2d(1, 2, 4, 60)
    a3 = align_3d()
    performance = 20 + 30*a1 + 25*a2 + 40*a3

    await update.message.reply_text(
        f"✅ تحلیل انجام شد!\n\n"
        f"🔸 هم‌ترازی انگیزه-وظیفه‌شناسی: {a1:.2f}\n"
        f"🔸 هم‌ترازی وظیفه‌شناسی-IQ: {a2:.2f}\n"
        f"🔸 هم‌ترازی ۳بعدی: {a3:.2f}\n"
        f"🎯 عملکرد پیش‌بینی‌شده تیم: {performance:.1f} از ۱۰۰"
    )
    return ConversationHandler.END

# لغو گفتگو
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("گفت‌وگو لغو شد. هر زمان خواستی /start رو بزن.")
    return ConversationHandler.END

# راه‌اندازی ربات
def main():
    import os
    TOKEN = os.environ.get("TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_MEMBERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_members)],
            COLLECT_FEATURES: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_features)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
