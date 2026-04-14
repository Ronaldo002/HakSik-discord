import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from keep_alive import keep_alive

# 1. 봇 권한 및 명령어 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ 시스템 가동 시작: {bot.user} 계정으로 로그인되었습니다.")

# 명령어 뒤에 'day'라는 변수를 추가로 받습니다. 기본값은 "오늘"입니다.
@bot.command(name='학식')
async def get_menu(ctx, day: str = "오늘"):
    kst = timezone(timedelta(hours=9))
    target_date = datetime.now(kst)
    
    # 사용자가 입력한 단어(내일, 모레)에 따라 날짜(target_date)를 하루, 이틀 뒤로 미룹니다.
    if day == "내일":
        target_date += timedelta(days=1)
        loading_msg = await ctx.send("🔍 내일 금정회관 메뉴를 조회 중입니다...")
    elif day == "모레":
        target_date += timedelta(days=2)
        loading_msg = await ctx.send("🔍 모레 금정회관 메뉴를 조회 중입니다...")
    else:
        loading_msg = await ctx.send("🔍 오늘 금정회관 메뉴를 조회 중입니다...")

    weekday = target_date.weekday()
    date_str = target_date.strftime("%Y년 %m월 %d일")
    weekdays_kr = ["월", "화", "수", "목", "금", "토", "일"]
    target_day_kr = weekdays_kr[weekday]

    url = "https://www.pusan.ac.kr/kor/CMS/MenuMgr/menuListOnBuilding.do?mCode=MN202"

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        target_menu = ""
        table = soup.find("table")
        
        if table:
            # [수직 낙하 알고리즘] 타겟 요일(오늘/내일/모레)이 몇 번째 기둥인지 확인
            target_col_index = -1
            thead = table.find("thead")
            headers = thead.find_all(["th", "td"]) if thead else table.find("tr").find_all(["th", "td"])
                
            for i, header in enumerate(headers):
                if target_day_kr in header.get_text():
                    target_col_index = i
                    break

            if target_col_index != -1:
                tbody = table.find("tbody") if table.find("tbody") else table
                for tr in tbody.find_all('tr'):
                    cells = tr.find_all(['th', 'td'])
                    
                    # 셀 병합(rowspan)으로 인한 칸 밀림 보정
                    actual_index = target_col_index
                    if len(cells) < len(headers):
                        diff = len(headers) - len(cells)
                        actual_index = target_col_index - diff
                    
                    if 0 <= actual_index < len(cells):
                        target_cell = cells[actual_index]
                        for br in target_cell.find_all("br"):
                            br.replace_with("\n")
                        menu_text = target_cell.get_text(separator="\n", strip=True)
                        
                        if menu_text:
                            # 메뉴 구분(중식 등) 추출
                            meal_type = "메뉴"
                            if cells[0] != target_cell: 
                                raw_type = cells[0].get_text(separator=" ", strip=True)
                                if len(raw_type) < 15: meal_type = raw_type
                            target_menu += f"[{meal_type}]\n{menu_text}\n\n"

        if not target_menu.strip():
            target_menu = "메뉴가 등록되지 않았거나 휴무입니다."

        # 메시지 포맷팅
        formatted_menu = ""
        for item in target_menu.strip().split('\n'):
            item = item.strip()
            if item:
                if item.startswith('[') and item.endswith(']'):
                    formatted_menu += f"\n**{item}**\n"
                else:
                    formatted_menu += f"> {item}\n"

        # 제목 동적 변경 (오늘의 학식 vs 내일의 학식)
        day_title = "내일의 학식" if day == "내일" else ("모레의 학식" if day == "모레" else "오늘의 학식")
        await loading_msg.edit(content=f"🍱 **[{day_title}] 금정회관 교직원 식당**\n📅 **{date_str} ({target_day_kr})**\n{formatted_menu}")

    except Exception as e:
        await loading_msg.edit(content=f"❌ 데이터 조회 중 오류가 발생했습니다: {e}")

# 2. 24시간 유지 기능 실행
keep_alive()

# -------------------------------------------------------------------
# ⚠️ 깃허브 업로드용 보안 코드
# -------------------------------------------------------------------
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ 에러: 환경 변수 'DISCORD_BOT_TOKEN'을 찾을 수 없습니다.")
