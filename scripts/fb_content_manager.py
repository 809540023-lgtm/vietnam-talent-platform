"""
Facebook 內容管理與排程工具
VietTalent - Facebook Content Manager

功能：
1. 自動生成中越雙語發文內容
2. 從職缺資料庫生成推廣文案
3. 排程發文（搭配 Meta Business Suite）
4. 管理發文模板
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ===== 發文模板 =====

TEMPLATES = {
    # ===== 職缺推廣模板 =====
    "job_posting": {
        "vi": """🔥 Cƨ HỘI VIỆC LÀM TẠI ĐÀI LOAN 🔥

💼 {title_vi}
🏢 Công ty: {company_name}
📍 Địa điểm: {location}
💰 Lương: {salary_min:,} - {salary_max:,} NTD/tháng

✅ Yêu cầu:
{requirements_vi}

🎁 Phúc lợi:
{benefits_vi}

📱 Ứng tuyển ngay:
🌐 Website: {website_url}
🤖 Telegram: {telegram_bot_url}

#VietTalentTW #ViệcLàmĐàiLoan #TuyểnDụng #NhânTàiViệtNam #{location_tag}
""",
        "zh": """🔥 越南人才招聘 🔥

💼 {title_zh}
🏢 公司：{company_name}
📍 地點：{location}
💰 薪資：{salary_min:,} - {salary_max:,} NTD/月

✅ 條件：
{requirements_zh}

🎁 福利：
{benefits_zh}

📱 立即應徵：
🌐 網站：{website_url}
🤖 Telegram：{telegram_bot_url}

#VietTalent #越南人才 #北北基職缺 #外籍勞工 #{location_tag}
"""
    },

    # ===== 平台推廣模板 =====
    "platform_promo": {
        "vi": """🇻🇳 BẠN ĐANG TÌM VIỆC LÀM TẠI ĐÀI LOAN? 🇹🇼

VietTalent Taiwan - Nền tảng tuyển dụng dành riêng cho người Việt!

✨ Tại sao chọn VietTalent?
✅ Giao diện 100% tiếng Việt
✅ Hàng trăm việc làm tại Bắc Đài Loan
✅ Đăng ký dễ dàng qua Telegram
✅ Tất cả nhà tuyển dụng đã xác minh
✅ Hoàn toàn MIỄN PHÍ

📱 Đăng ký ngay:
🌐 {website_url}
🤖 Telegram: {telegram_bot_url}

Chia sẻ cho bạn bè đang cần tìm việc nhé! 🤝

#VietTalentTW #ViệcLàmĐàiLoan #NgườiViệtTạiĐàiLoan
""",
        "zh": """🇻🇳 尋找越南人才？就在 VietTalent Taiwan！🇹🇼

專為越南人才打造的招聘平台

✨ 我們的優勢：
✅ 越南文介面，無語言障礙
✅ 北北基地區大量求職者
✅ Telegram 即時互動
✅ 所有求職者資料已驗證
✅ 企業刊登職缺免費

📱 立即加入：
🌐 {website_url}

歡迎分享給有越南人才需求的企業！

#VietTalent #越南人才 #人力資源 #北北基
"""
    },

    # ===== 生活分享模板 =====
    "life_tips": {
        "vi": """📚 {tip_title_vi}

{tip_content_vi}

💡 Bạn có kinh nghiệm gì muốn chia sẻ không? Comment bên dưới nhé!

📱 Theo dõi VietTalent để nhận thêm thông tin hữu ích:
🌐 {website_url}
🤖 Telegram: {telegram_bot_url}

#VietTalentTW #NgườiViệtTạiĐàiLoan #CuộcSốngĐàiLoan
""",
    },

    # ===== 週報模板 =====
    "weekly_digest": {
        "vi": """📊 TỔNG KẾT TUẦN - VietTalent Taiwan

📅 Tuần {week_number}, {year}

🆕 Việc làm mới: {new_jobs} vị trí
👥 Ứng viên mới: {new_candidates} người
🤝 Tuyển dụng thành công: {hired} người

🔥 TOP VIỆC LÀM TUẦN NÀY:
{top_jobs}

📱 Xem thêm tại: {website_url}

#VietTalentTW #BáoCáoTuần
""",
        "zh": """📊 VietTalent 每週報告

📅 {year} 年第 {week_number} 週

🆕 新增職缺：{new_jobs} 個
👥 新增求職者：{new_candidates} 人
🤝 成功媒合：{hired} 人

🔥 本週熱門職缺：
{top_jobs}

📱 詳情請見：{website_url}

#VietTalent #週報 #越南人才
"""
    },
}

# ===== 常用生活小知識 =====
LIFE_TIPS = [
    {
        "title_vi": "Cách đi tàu MRT tại Đài Loan",
        "content_vi": "MRT là phương tiện đi lại tiện lợi nhất tại Đài Bắc. Bạn có thể mua thẻ EasyCard tại các ga MRT hoặc cửa hàng tiện lợi với giá 100 NTD. Thẻ này có thể dùng cho tàu, xe buýt và mua sắm tại các cửa hàng tiện lợi.",
    },
    {
        "title_vi": "Quyền lợi lao động tại Đài Loan",
        "content_vi": "Theo luật lao động Đài Loan, người lao động nước ngoài có quyền: lương tối thiểu 27,470 NTD/tháng, bảo hiểm lao động và y tế, ngày nghỉ phép theo quy định, tiền tăng ca. Nếu gặp vấn đề, hãy gọi đường dây nóng 1955 (có phiên dịch tiếng Việt).",
    },
    {
        "title_vi": "Những ứng dụng hữu ích cho người Việt tại Đài Loan",
        "content_vi": "1. Google Maps - Tìm đường\n2. Google Translate - Dịch tiếng\n3. LINE - Nhắn tin phổ biến nhất\n4. FoodPanda - Đặt đồ ăn\n5. 7-11/FamilyMart App - Ưu đãi cửa hàng tiện lợi\n6. EasyWallet - Quản lý EasyCard",
    },
    {
        "title_vi": "Cách gửi tiền về Việt Nam từ Đài Loan",
        "content_vi": "Có nhiều cách gửi tiền về Việt Nam: qua ngân hàng (phí cao nhưng an toàn), qua các dịch vụ chuyển tiền như Western Union, hoặc qua ứng dụng như Wise, Remitly. So sánh tỷ giá và phí trước khi chuyển nhé!",
    },
]


class FacebookContentManager:
    """Facebook 內容管理器"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.website_url = self.config.get('website_url', 'https://viettalent.tw')
        self.telegram_bot_url = self.config.get('telegram_bot_url', 'https://t.me/VietTalentTW_bot')
        self.scheduled_posts: List[Dict] = []

    def generate_job_post(self, job_data: Dict, lang: str = "both") -> Dict[str, str]:
        """從職缺資料生成 Facebook 發文"""
        location_map = {
            "台北": "ĐàiBắc", "新北": "TânBắc",
            "基隆": "CơLong", "桃園": "ĐàoViên",
        }

        params = {
            **job_data,
            "website_url": self.website_url,
            "telegram_bot_url": self.telegram_bot_url,
            "location_tag": location_map.get(job_data.get('location', ''), 'ĐàiLoan'),
        }

        result = {}
        template = TEMPLATES["job_posting"]

        if lang in ("vi", "both"):
            try:
                result["vi"] = template["vi"].format(**params)
            except KeyError as e:
                result["vi"] = f"[模板缺少欄位: {e}]"

        if lang in ("zh", "both"):
            try:
                result["zh"] = template["zh"].format(**params)
            except KeyError as e:
                result["zh"] = f"[模板缺少欄位: {e}]"

        return result

    def generate_promo_post(self, lang: str = "both") -> Dict[str, str]:
        """生成平台推廣發文"""
        params = {
            "website_url": self.website_url,
            "telegram_bot_url": self.telegram_bot_url,
        }
        result = {}
        template = TEMPLATES["platform_promo"]

        if lang in ("vi", "both") and "vi" in template:
            result["vi"] = template["vi"].format(**params)
        if lang in ("zh", "both") and "zh" in template:
            result["zh"] = template["zh"].format(**params)

        return result

    def generate_weekly_digest(self, stats: Dict, top_jobs: List[Dict]) -> Dict[str, str]:
        """生成週報"""
        now = datetime.now()
        top_jobs_vi = "\n".join([
            f"  {i+1}. {j.get('title_vi', j.get('title_zh', ''))} - ${j.get('salary_min', 0):,}+"
            for i, j in enumerate(top_jobs[:5])
        ])
        top_jobs_zh = "\n".join([
            f"  {i+1}. {j.get('title_zh', '')} - ${j.get('salary_min', 0):,}+"
            for i, j in enumerate(top_jobs[:5])
        ])

        params = {
            "week_number": now.isocalendar()[1],
            "year": now.year,
            "new_jobs": stats.get("new_jobs", 0),
            "new_candidates": stats.get("new_candidates", 0),
            "hired": stats.get("hired", 0),
            "website_url": self.website_url,
        }

        template = TEMPLATES["weekly_digest"]
        return {
            "vi": template["vi"].format(**params, top_jobs=top_jobs_vi),
            "zh": template["zh"].format(**params, top_jobs=top_jobs_zh),
        }

    def generate_life_tip(self, tip_index: int = 0) -> Dict[str, str]:
        """生成生活小知識發文"""
        tip = LIFE_TIPS[tip_index % len(LIFE_TIPS)]
        params = {
            **tip,
            "website_url": self.website_url,
            "telegram_bot_url": self.telegram_bot_url,
        }
        template = TEMPLATES["life_tips"]
        return {
            "vi": template["vi"].format(**params),
        }

    def schedule_post(self, content: Dict[str, str], scheduled_time: datetime,
                     platform: str = "facebook", post_type: str = "job_posting"):
        """排程發文"""
        post = {
            "content": content,
            "scheduled_time": scheduled_time.isoformat(),
            "platform": platform,
            "post_type": post_type,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }
        self.scheduled_posts.append(post)
        return post

    def generate_weekly_schedule(self) -> List[Dict]:
        """生成一週的發文排程"""
        schedule = []
        now = datetime.now()

        # 週一：平台推廣
        monday = now + timedelta(days=(7 - now.weekday()) % 7)
        monday = monday.replace(hour=10, minute=0, second=0)
        schedule.append({
            "day": "Monday / Thứ Hai",
            "time": "10:00",
            "type": "platform_promo",
            "description": "平台推廣 / Quảng bá nền tảng",
        })

        # 週二、四：職缺推廣
        for day_name, offset in [("Tuesday / Thứ Ba", 1), ("Thursday / Thứ Năm", 3)]:
            schedule.append({
                "day": day_name,
                "time": "11:00",
                "type": "job_posting",
                "description": "職缺推廣 / Đăng tin tuyển dụng",
            })

        # 週三：生活小知識
        schedule.append({
            "day": "Wednesday / Thứ Tư",
            "time": "14:00",
            "type": "life_tips",
            "description": "生活小知識 / Mẹo cuộc sống",
        })

        # 週五：週報
        schedule.append({
            "day": "Friday / Thứ Sáu",
            "time": "17:00",
            "type": "weekly_digest",
            "description": "週報 / Tổng kết tuần",
        })

        return schedule

    def export_schedule(self, filepath: str = "content_schedule.json"):
        """匯出排程為 JSON"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "weekly_schedule": self.generate_weekly_schedule(),
            "scheduled_posts": self.scheduled_posts,
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath


# ===== 目標 Facebook 社團清單 =====
TARGET_GROUPS = [
    {
        "name": "CỘNG ĐỒNG NGƯỜI VIỆT TẠI ĐÀI LOAN",
        "url": "https://facebook.com/groups/vietnam.taiwan.community",
        "members": "50,000+",
        "type": "general",
        "note": "越南人在台灣社群 - 綜合社團",
    },
    {
        "name": "越南妹台灣仔",
        "url": "https://facebook.com/groups/505911482905057",
        "members": "30,000+",
        "type": "general",
        "note": "越南人台灣社群",
    },
    {
        "name": "Jobs in Taiwan for Foreign Talents",
        "url": "https://facebook.com/groups/cake.job.global",
        "members": "20,000+",
        "type": "jobs",
        "note": "外國人找工作專用社團",
    },
    {
        "name": "TAIWAN HIRING / FACTORY WORKERS",
        "url": "https://facebook.com/groups/637404863779871",
        "members": "15,000+",
        "type": "jobs",
        "note": "工廠招工社團",
    },
    {
        "name": "Community & Jobs Board For Vietnam Remote Workers",
        "url": "https://facebook.com/groups/vietassist",
        "members": "10,000+",
        "type": "jobs",
        "note": "越南遠端工作者社群",
    },
]


def demo():
    """展示功能"""
    manager = FacebookContentManager()

    print("=" * 60)
    print("VietTalent - Facebook Content Manager Demo")
    print("=" * 60)

    # 1. 生成職缺發文
    job = {
        "title_vi": "Công nhân nhà máy điện tử",
        "title_zh": "電子廠作業員",
        "company_name": "ABC Electronics",
        "location": "新北",
        "salary_min": 32000,
        "salary_max": 38000,
        "requirements_vi": "• Tuổi 20-45\n• Không cần kinh nghiệm\n• Có thể tăng ca",
        "requirements_zh": "• 20-45歲\n• 免經驗\n• 可配合加班",
        "benefits_vi": "• Có nhà ở miễn phí\n• Có bữa ăn\n• Bảo hiểm đầy đủ\n• Thưởng lễ tết",
        "benefits_zh": "• 免費宿舍\n• 供餐\n• 勞健保\n• 三節獎金",
    }

    posts = manager.generate_job_post(job)
    print("\n📝 職缺發文（越南文）:")
    print("-" * 40)
    print(posts.get("vi", ""))

    # 2. 生成推廣發文
    promo = manager.generate_promo_post()
    print("\n📢 平台推廣（越南文）:")
    print("-" * 40)
    print(promo.get("vi", ""))

    # 3. 顯示排程
    schedule = manager.generate_weekly_schedule()
    print("\n📅 每週發文排程:")
    print("-" * 40)
    for item in schedule:
        print(f"  {item['day']} {item['time']} - {item['description']}")

    # 4. 顯示目標社團
    print("\n🎯 目標 Facebook 社圚:")
    print("-" * 40)
    for group in TARGET_GROUPS:
        print(f"  • {group['name']} ({group['members']} members)")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo()
