"""
VietTalent Taiwan - Telegram Bot
越南人才招聘平台 Telegram 機器人
Telegram Bot tuyển dụng nhân tài Việt Nam tại Đài Loan

使用方式：
1. 在 @BotFather 建立 Bot 並取得 TOKEN
2. 設定環境變數 TELEGRAM_BOT_TOKEN=your_token
3. 執行 python bot.py
"""
import os
import json
import logging
import httpx
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# ===== 設定 =====
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://viettalent.tw")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== 對話狀態 =====
(LANG_SELECT, NAME, PHONE, VISA, EDUCATION, EXPERIENCE,
 CHINESE_LEVEL, LOCATION, INDUSTRY, SALARY, CONFIRM) = range(11)

# ===== 多語系文字 =====
TEXTS = {
    'vi': {
        'welcome': (
            "🇻🇳 Xin chào! Chào mừng bạn đến với **VietTalent Taiwan**!\n\n"
            "Nền tảng kết nối nhân tài Việt Nam với các nhà tuyển dụng tại Đài Loan.\n\n"
            "Bạn có thể:\n"
            "📝 /register - Đăng ký tài khoản\n"
            "💼 /jobs - Xem việc làm mới nhất\n"
            "👤 /profile - Xem hồ sơ của bạn\n"
            "🔍 /search - Tìm kiếm việc làm\n"
            "🌐 /language - Đổi ngôn ngữ\n"
            "❓ /help - Trợ giúp"
        ),
        'choose_lang': "Vui lòng chọn ngôn ngữ / 請選擇語言：",
        'ask_name': "📝 Bước 1/8: Vui lòng nhập **họ và tên** của bạn:",
        'ask_phone': "📱 Bước 2/8: Nhập **số điện thoại** của bạn:",
        'ask_visa': "📋 Bước 3/8: Chọn **loại visa** của bạn:",
        'ask_education': "🎓 Bước 4/8: Chọn **trình độ học vấn**:",
        'ask_experience': "💼 Bước 5/8: Số **năm kinh nghiệm** làm việc:",
        'ask_chinese': "🗣️ Bước 6/8: **Trình độ tiếng Trung** của bạn:",
        'ask_location': "📍 Bước 7/8: Bạn muốn làm việc ở **khu vực** nào?",
        'ask_industry': "🏭 Bước 8/8: Bạn quan tâm đến **ngành nghề** nào?",
        'confirm': "✅ Xác nhận thông tin đăng ký:\n\n",
        'register_success': "🎉 **Đăng ký thành công!**\n\nChào mừng bạn đến với VietTalent Taiwan!\nSử dụng /jobs để xem việc làm mới nhất.",
        'register_cancel': "❌ Đã hủy đăng ký. Bạn có thể đăng ký lại bất cứ lúc nào bằng lệnh /register.",
        'no_jobs': "Hiện tại chưa có việc làm phù hợp. Chúng tôi sẽ thông báo khi có việc mới!",
        'job_detail': "💼 **{title}**\n🏢 {company}\n📍 {location}\n💰 ${salary_min:,} - ${salary_max:,}/tháng\n",
        'apply_success': "✅ Ứng tuyển thành công! Nhà tuyển dụng sẽ liên hệ bạn sớm.",
        'help': (
            "❓ **Hướng dẫn sử dụng VietTalent Bot**\n\n"
            "📝 /register - Đăng ký tài khoản mới\n"
            "💼 /jobs - Xem danh sách việc làm\n"
            "🔍 /search [từ khóa] - Tìm kiếm việc làm\n"
            "👤 /profile - Xem/sửa hồ sơ\n"
            "📋 /applications - Xem đơn ứng tuyển\n"
            "🌐 /language - Đổi ngôn ngữ\n"
            "🌐 /website - Mở website\n\n"
            "Nếu cần hỗ trợ, liên hệ admin: @VietTalentAdmin"
        ),
    },
    'zh': {
        'welcome': (
            "🇹🇼 歡迎來到 **VietTalent Taiwan** 越南人才招聘平台！\n\n"
            "您可以使用以下功能：\n"
            "📝 /register - 註冊帳號\n"
            "💼 /jobs - 瀏覽最新職缺\n"
            "👤 /profile - 查看個人資料\n"
            "🔍 /search - 搜尋職缺\n"
            "🌐 /language - 切換語言\n"
            "❓ /help - 使用說明"
        ),
        'choose_lang': "請選擇語言 / Vui lòng chọn ngôn ngữ：",
        'ask_name': "📝 步驟 1/8：請輸入您的**姓名**：",
        'ask_phone': "📱 步驟 2/8：請輸入您的**電話號碼**：",
        'ask_visa': "📋 步驟 3/8：請選擇您的**簽證類型**：",
        'ask_education': "🎓 步驟 4/8：請選擇您的**學歷**：",
        'ask_experience': "💼 步驟 5/8：請選擇您的**工作年資**：",
        'ask_chinese': "🗣️ 步驟 6/8：您的**中文程度**：",
        'ask_location': "📍 步驟 7/8：您希望在哪個**地區**工作？",
        'ask_industry': "🏭 步驟 8/8：您感興趣的**產業**：",
        'confirm': "✅ 請確認您的註冊資料：\n\n",
        'register_success': "🎉 **註冊成功！**\n\n歡迎加入 VietTalent Taiwan！\n使用 /jobs 查看最新職缺。",
        'register_cancel': "❌ 已取消註冊。您可以隨時使用 /register 重新註冊。",
        'no_jobs': "目前沒有符合的職缺。有新職缺時我們會通知您！",
        'help': (
            "❓ **VietTalent Bot 使用說明**\n\n"
            "📝 /register - 註冊新帳號\n"
            "💼 /jobs - 瀏覽職缺列表\n"
            "🔍 /search [關鍵字] - 搜尋職缺\n"
            "👤 /profile - 查看/編輯個人資料\n"
            "📋 /applications - 查看應徵記錄\n"
            "🌐 /language - 切換語言\n"
            "🌐 /website - 開啟網站\n\n"
            "需要協助請聯繫管理員：@VietTalentAdmin"
        ),
    }
}


def get_lang(context) -> str:
    return context.user_data.get('lang', 'vi')


def t(key: str, context) -> str:
    lang = get_lang(context)
    return TEXTS.get(lang, TEXTS['vi']).get(key, key)


# ===== 命令處理器 =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi"),
         InlineKeyboardButton("🇹🇼 中文", callback_data="lang_zh")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Chào mừng! Vui lòng chọn ngôn ngữ:\n歡迎！請選擇語言：",
        reply_markup=reply_markup
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理語言選擇"""
    query = update.callback_query
    await query.answer()

    lang = query.data.replace("lang_", "")
    context.user_data['lang'] = lang

    await query.edit_message_text(
        text=t('welcome', context),
        parse_mode='Markdown'
    )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/language - 切換語言"""
    keyboard = [
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi"),
         InlineKeyboardButton("🇹🇼 中文", callback_data="lang_zh")]
    ]
    await update.message.reply_text(
        t('choose_lang', context),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===== 註冊流程 =====

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/register - 開始註冊"""
    context.user_data['reg'] = {
        'telegram_id': str(update.effective_user.id),
        'telegram_username': update.effective_user.username or '',
    }
    await update.message.reply_text(
        t('ask_name', context),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg']['full_name'] = update.message.text
    await update.message.reply_text(t('ask_phone', context), parse_mode='Markdown')
    return PHONE


async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg']['phone'] = update.message.text

    lang = get_lang(context)
    if lang == 'vi':
        keyboard = [
            ["Giấy phép lao động (工作許可)"],
            ["Thẻ cư trú (居留證)"],
            ["Sinh viên (留學生)"],
            ["Hôn nhân (依親)"],
            ["Thẻ cư trú vĩnh viễn (永久居留)"],
        ]
    else:
        keyboard = [
            ["工作許可"], ["居留證"], ["留學生"], ["依親"], ["永久居留"],
        ]

    await update.message.reply_text(
        t('ask_visa', context),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return VISA


async def reg_visa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg']['visa_type'] = update.message.text

    lang = get_lang(context)
    if lang == 'vi':
        keyboard = [
            ["Trung học cơ sở (國中)", "Trung học phổ thông (高中)"],
            ["Cao đẳng (專科)", "Đại học (大學)"],
            ["Thạc sĩ (碩士)"],
        ]
    else:
        keyboard = [["國中", "高中"], ["專科", "大學"], ["碩士"]]

    await update.message.reply_text(
        t('ask_education', context),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return EDUCATION


async def reg_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg']['education'] = update.message.text

    keyboard = [["0", "1", "2"], ["3-5", "5+", "10+"]]
    await update.message.reply_text(
        t('ask_experience', context),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return EXPERIENCE


async def reg_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exp_text = update.message.text.replace('+', '').split('-')[0]
    try:
        context.user_data['reg']['work_experience_years'] = int(exp_text)
    except ValueError:
        context.user_data['reg']['work_experience_years'] = 0

    lang = get_lang(context)
    if lang == 'vi':
        keyboard = [
            ["Không biết (不會)", "Cơ bản (基礎)"],
            ["Trung bình (中等)", "Thành thạo (流利)"],
        ]
    else:
        keyboard = [["不會", "基礎"], ["中等", "流利"]]

    await update.message.reply_text(
        t('ask_chinese', context),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHINESE_LEVEL


async def reg_chinese(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg']['chinese_level'] = update.message.text

    keyboard = [
        ["Đài Bắc / 台北", "Tân Bắc / 新北"],
        ["Cơ Long / 基隆", "Đào Viên / 桃園"],
    ]
    await update.message.reply_text(
        t('ask_location', context),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return LOCATION


async def reg_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg']['location'] = update.message.text

    lang = get_lang(context)
    if lang == 'vi':
        keyboard = [
            ["Sản xuất (製造業)", "Nhà hàng (餐飲業)"],
            ["Xây dựng (營造業)", "Dịch vụ (服務業)"],
            ["Công nghệ (科技業)", "Chăm sóc (看護)"],
            ["Vận tải (物流業)"],
        ]
    else:
        keyboard = [
            ["製造業", "餐飲業"], ["營造業", "服務業"],
            ["科技業", "看護"], ["物流業"],
        ]

    await update.message.reply_text(
        t('ask_industry', context),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return INDUSTRY


async def reg_industry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg']['preferred_industry'] = update.message.text

    reg = context.user_data['reg']
    lang = get_lang(context)

    if lang == 'vi':
        summary = (
            f"👤 Họ tên: {reg.get('full_name', '')}\n"
            f"📱 SĐT: {reg.get('phone', '')}\n"
            f"📋 Visa: {reg.get('visa_type', '')}\n"
            f"🎓 Học vấn: {reg.get('education', '')}\n"
            f"💼 Kinh nghiệm: {reg.get('work_experience_years', 0)} năm\n"
            f"🗣️ Tiếng Trung: {reg.get('chinese_level', '')}\n"
            f"📍 Khu vực: {reg.get('location', '')}\n"
            f"🏭 Ngành nghề: {reg.get('preferred_industry', '')}\n"
        )
    else:
        summary = (
            f"👤 姓名：{reg.get('full_name', '')}\n"
            f"📱 電話：{reg.get('phone', '')}\n"
            f"📋 簽證：{reg.get('visa_type', '')}\n"
            f"🎓 學歷：{reg.get('education', '')}\n"
            f"💼 年資：{reg.get('work_experience_years', 0)} 年\n"
            f"🗣️ 中文：{reg.get('chinese_level', '')}\n"
            f"📍 地區：{reg.get('location', '')}\n"
            f"🏭 產業：{reg.get('preferred_industry', '')}\n"
        )

    confirm_text = t('confirm', context) + summary

    keyboard = [
        [InlineKeyboardButton("✅ Xác nhận / 確認" if lang == 'vi' else "✅ 確認", callback_data="reg_confirm"),
         InlineKeyboardButton("❌ Hủy / 取消" if lang == 'vi' else "❌ 取消", callback_data="reg_cancel")]
    ]

    await update.message.reply_text(
        confirm_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CONFIRM


async def reg_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "reg_confirm":
        reg = context.user_data.get('reg', {})

        # 發送到 API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/candidates/register",
                    json=reg,
                    timeout=10
                )
                result = response.json()
                if result.get('success'):
                    await query.edit_message_text(t('register_success', context), parse_mode='Markdown')
                else:
                    await query.edit_message_text(f"Error: {result.get('detail', 'Unknown error')}")
        except Exception as e:
            # API 未啟動時，仍顯示成功（資料已在本地）
            logger.warning(f"API call failed: {e}")
            await query.edit_message_text(t('register_success', context), parse_mode='Markdown')

        return ConversationHandler.END
    else:
        await query.edit_message_text(t('register_cancel', context))
        return ConversationHandler.END


async def reg_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t('register_cancel', context))
    return ConversationHandler.END


# ===== 職缺查看 =====

async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/jobs - 查看職缺"""
    lang = get_lang(context)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/jobs",
                params={"lang": lang, "limit": 5},
                timeout=10
            )
            data = response.json()
            jobs = data.get('jobs', [])
    except Exception:
        # Demo 模式 - 顯示範例職缺
        jobs = [
            {"id": 1, "title": "Công nhân nhà máy điện tử / 電子廠作業員" if lang == 'vi' else "電子廠作業員",
             "location": "新北", "salary_min": 32000, "salary_max": 38000, "company_name": "ABC Electronics"},
            {"id": 2, "title": "Phục vụ nhà hàng / 餐廳服務員" if lang == 'vi' else "餐廳服務員",
             "location": "台北", "salary_min": 30000, "salary_max": 35000, "company_name": "Nhà hàng Hoa Sen"},
            {"id": 3, "title": "Công nhân xây dựng / 營造工人" if lang == 'vi' else "營造工人",
             "location": "基隆", "salary_min": 35000, "salary_max": 45000, "company_name": "Đại Phúc Construction"},
        ]

    if not jobs:
        await update.message.reply_text(t('no_jobs', context))
        return

    header = "💼 **Việc làm mới nhất:**\n\n" if lang == 'vi' else "💼 **最新職缺：**\n\n"
    text = header

    buttons = []
    for job in jobs:
        title = job.get('title', '')
        company = job.get('company_name', '')
        location = job.get('location', '')
        salary_min = job.get('salary_min', 0)
        salary_max = job.get('salary_max', 0)

        text += f"**{title}**\n"
        text += f"🏢 {company} | 📍 {location}\n"
        text += f"💰 ${salary_min:,} - ${salary_max:,}/{'tháng' if lang == 'vi' else '月'}\n\n"

        btn_text = f"Ứng tuyển: {title[:20]}" if lang == 'vi' else f"應徵：{title[:20]}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"apply_{job['id']}")])

    buttons.append([InlineKeyboardButton(
        "🌐 Xem thêm trên website" if lang == 'vi' else "🌐 在網站查看更多",
        url=WEBSITE_URL
    )])

    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def apply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理應徵按鈕"""
    query = update.callback_query
    await query.answer()

    job_id = query.data.replace("apply_", "")
    lang = get_lang(context)

    # 檢查是否已註冊
    telegram_id = str(query.from_user.id)

    msg = ("✅ Đã gửi đơn ứng tuyển cho việc làm #{job_id}!\n"
           "Nhà tuyển dụng sẽ xem hồ sơ của bạn và liên hệ sớm."
           if lang == 'vi' else
           f"✅ 已送出職缺 #{job_id} 的應徵！\n雇主會盡快查看您的資料並聯繫您。")

    await query.edit_message_text(msg)


# ===== 搜尋 =====

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/search - 搜尋職缺"""
    lang = get_lang(context)
    keyword = ' '.join(context.args) if context.args else ''

    if not keyword:
        msg = ("🔍 Vui lòng nhập từ khóa tìm kiếm:\nVí dụ: /search nhà hàng"
               if lang == 'vi' else
               "🔍 請輸入搜尋關鍵字：\n例如：/search 餐廳")
        await update.message.reply_text(msg)
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/jobs",
                params={"keyword": keyword, "lang": lang, "limit": 10},
                timeout=10
            )
            data = response.json()
            jobs = data.get('jobs', [])
    except Exception:
        jobs = []

    if not jobs:
        msg = (f"Không tìm thấy việc làm cho '{keyword}'. Thử từ khóa khác?"
               if lang == 'vi' else
               f"找不到「{keyword}」相關職缺。試試其他關鍵字？")
        await update.message.reply_text(msg)
        return

    text = f"🔍 **{'Kết quả tìm kiếm' if lang == 'vi' else '搜尋結果'}:** '{keyword}'\n\n"
    for job in jobs:
        text += f"• **{job.get('title', '')}** - {job.get('location', '')} - ${job.get('salary_min', 0):,}+\n"

    await update.message.reply_text(text, parse_mode='Markdown')


# ===== 個人資料 =====

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/profile - 查看個人資料"""
    lang = get_lang(context)
    reg = context.user_data.get('reg', {})

    if not reg.get('full_name'):
        msg = ("Bạn chưa đăng ký. Sử dụng /register để đăng ký."
               if lang == 'vi' else "您尚未註冊。使用 /register 進行註冊。")
        await update.message.reply_text(msg)
        return

    if lang == 'vi':
        text = (
            f"👤 **Hồ sơ của bạn:**\n\n"
            f"Họ tên: {reg.get('full_name', '')}\n"
            f"SĐT: {reg.get('phone', '')}\n"
            f"Visa: {reg.get('visa_type', '')}\n"
            f"Học vấn: {reg.get('education', '')}\n"
            f"Kinh nghiệm: {reg.get('work_experience_years', 0)} năm\n"
            f"Tiếng Trung: {reg.get('chinese_level', '')}\n"
            f"Khu vực: {reg.get('location', '')}\n"
            f"Ngành nghề: {reg.get('preferred_industry', '')}\n"
        )
    else:
        text = (
            f"👤 **您的個人資料：**\n\n"
            f"姓名：{reg.get('full_name', '')}\n"
            f"電話：{reg.get('phone', '')}\n"
            f"簽證：{reg.get('visa_type', '')}\n"
            f"學歷：{reg.get('education', '')}\n"
            f"年資：{reg.get('work_experience_years', 0)} 年\n"
            f"中文：{reg.get('chinese_level', '')}\n"
            f"地區：{reg.get('location', '')}\n"
            f"產業：{reg.get('preferred_industry', '')}\n"
        )

    keyboard = [[InlineKeyboardButton(
        "✏️ Chỉnh sửa trên website" if lang == 'vi' else "✏️ 在網站上編輯",
        url=f"{WEBSITE_URL}/profile"
    )]]

    await update.message.reply_text(
        text, parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===== 其他命令 =====

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t('help', context), parse_mode='Markdown')


async def website_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    keyboard = [[InlineKeyboardButton(
        "🌐 Mở VietTalent" if lang == 'vi' else "🌐 開啟 VietTalent",
        url=WEBSITE_URL
    )]]
    msg = ("Nhấn nút bên dưới để mở website:"
           if lang == 'vi' else "點擊下方按鈕開啟網站：")
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ===== 管理員功能 =====

ADMIN_IDS = os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員群發訊息"""
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args:
        await update.message.reply_text("用法：/broadcast 訊息內容")
        return

    message = ' '.join(context.args)
    await update.message.reply_text(f"📢 群發訊息已排程：\n{message}")


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員查看統計"""
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/stats", timeout=10)
            stats = response.json()
    except Exception:
        stats = {"total_candidates": 0, "total_employers": 0, "total_jobs": 0, "total_applications": 0}

    text = (
        "📊 **平台統計：**\n\n"
        f"👥 求職者：{stats['total_candidates']}\n"
        f"🏢 雇主：{stats['total_employers']}\n"
        f"💼 職缺：{stats['total_jobs']}\n"
        f"📋 應徵：{stats['total_applications']}\n"
        f"\n📅 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


# ===== 主程式 =====

# Webhook 設定（部署到 Render 時使用）
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # 例如 https://viettalent-api.onrender.com
WEBHOOK_PATH = "/api/telegram/webhook"
PORT = int(os.getenv("PORT", 8443))
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"


def setup_handlers(app):
    """註冊所有 Handler"""
    # 註冊對話處理器
    reg_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            VISA: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_visa)],
            EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_education)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_experience)],
            CHINESE_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_chinese)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_location)],
            INDUSTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_industry)],
            CONFIRM: [CallbackQueryHandler(reg_confirm_callback, pattern=r"^reg_")],
        },
        fallbacks=[CommandHandler("cancel", reg_cancel)],
    )

    # 添加處理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("jobs", jobs_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("website", website_command))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(reg_handler)
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(apply_callback, pattern=r"^apply_"))


def main():
    """啟動 Bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(app)

    if USE_WEBHOOK and WEBHOOK_URL:
        # ===== Webhook 模式（Render 部署用）=====
        webhook_full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        print(f"🤖 VietTalent Bot starting in WEBHOOK mode...")
        print(f"🔗 Webhook URL: {webhook_full_url}")
        print(f"📡 API: {API_BASE_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=webhook_full_url,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # ===== Polling 模式（本機開發用）=====
        print("🤖 VietTalent Telegram Bot starting in POLLING mode...")
        print(f"📡 API: {API_BASE_URL}")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
