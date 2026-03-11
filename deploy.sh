#!/bin/bash
# =============================================
# VietTalent Taiwan - ä¸éµé¨ç½²è³æ¬
# ä½¿ç¨æ¹å¼ï¼
#   chmod +x deploy.sh
#   ./deploy.sh
# =============================================

set -e

echo "ð VietTalent Taiwan - é¨ç½²è³æ¬"
echo "================================="
echo ""

# æª¢æ¥ git
if ! command -v git &> /dev/null; then
    echo "â è«åå®è£ git: https://git-scm.com/downloads"
    exit 1
fi

# æª¢æ¥ gh CLI
if ! command -v gh &> /dev/null; then
    echo "â ï¸  GitHub CLI æªå®è£"
    echo "   å®è£æ¹å¼ï¼"
    echo "   Mac:     brew install gh"
    echo "   Windows: winget install --id GitHub.cli"
    echo "   Linux:   https://cli.github.com/"
    echo ""
    echo "å®è£å¾å·è¡: gh auth login"
    exit 1
fi

# æª¢æ¥ GitHub ç»å¥çæ
if ! gh auth status &> /dev/null 2>&1; then
    echo "ð è«åç»å¥ GitHub..."
    gh auth login
fi

# åå¾ GitHub ç¨æ¶å
GH_USER=$(gh api user --jq '.login')
REPO_NAME="vietnam-talent-platform"

echo "ð¤ GitHub ç¨æ¶: $GH_USER"
echo "ð¦ ååº«åç¨±: $REPO_NAME"
echo ""

# å»ºç« GitHub ååº«
echo "ð¦ æ­£å¨å»ºç« GitHub ååº«..."
gh repo create "$REPO_NAME" --public --description "ð»ð³ Vietnamese Talent Platform in Taiwan - è¶åäººææèå¹³å° - Ná»n táº£ng tuyá»n dá»¥ng nhÃ¢n tÃ i Viá»t Nam táº¡i ÄÃ i Loan" 2>/dev/null || echo "ååº«å·²å­å¨ï¼ç¹¼çºæ¨é..."

# è¨­å® remote ä¸¦æ¨é
echo "â¬ï¸  æ­£å¨æ¨éå° GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$GH_USER/$REPO_NAME.git"
git push -u origin main

echo ""
echo "â GitHub æ¨éæåï¼"
echo "ð ååº«ç¶²å: https://github.com/$GH_USER/$REPO_NAME"
echo ""

# è©¢åæ¯å¦é¨ç½²å° Render
echo "================================="
echo "æ¥ä¸ä¾¦é¨ç½²å° Renderï¼"
echo ""
echo "æ¹æ³ 1: ä½¿ç¨ Render Blueprintï¼æ¨è¦ï¼"
echo "  æéï¼https://render.com/deploy"
echo "  è²¼ä¸ï¼https://github.com/$GH_USER/$REPO_NAME"
echo ""
echo "æ¹æ³ 2: æåé¨ç½²"
echo "  1. å° https://dashboard.render.com"
echo "  2. New â Web Service"
echo "  3. é£æ¥ GitHub ååº«: $REPO_NAME"
echo "  4. è¨­å®ï¼"
echo "     Build Command: pip install -r requirements.txt"
echo "     Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port \$PORT"
echo ""
echo "  5. ç°å¢è®æ¸ï¼å¨ Render è¨­å®ï¼ï¼"
echo "     TELEGRAM_BOT_TOKEN=ä½ çTelegram Bot Token"
echo "     GOOGLE_TRANSLATE_API_KEY=ï¼å¯é¸ï¼"
echo ""

echo "ð é¨ç½²è³æ¬å®æï¼"
