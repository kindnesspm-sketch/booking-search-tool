from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import urllib.parse
import re
import pandas as pd

def get_booking_count_per_day(location, start_date_str, end_date_str):
    """
    使用 Playwright 根據起始與結束日期，逐日抓取 Booking.com 住宿數量並匯出 Excel
    """
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        print("日期格式錯誤，請使用 YYYY-MM-DD")
        return

    if end_date <= start_date:
        print("錯誤：結束日期必須晚於起始日期。")
        return

    # 計算總天數
    total_days = (end_date - start_date).days
    results_list = []
    
    # 啟動 Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        print(f"=== 開始逐日搜尋：{location} ===")
        print(f"時段：{start_date_str} 至 {end_date_str} (共 {total_days} 筆搜尋)")
        
        for i in range(total_days):
            current_checkin_date = start_date + timedelta(days=i)
            current_checkout_date = current_checkin_date + timedelta(days=1)
            
            checkin_str = current_checkin_date.strftime("%Y-%m-%d")
            checkout_str = current_checkout_date.strftime("%Y-%m-%d")
            
            # 構建 URL
            base_url = "https://www.booking.com/searchresults.zh-tw.html"
            params = {
                "ss": location,
                "checkin": checkin_str,
                "checkout": checkout_str,
                "group_adults": 2,
                "no_rooms": 1,
                "group_children": 0,
                "sb_travel_purpose": "leisure",
                "selected_currency": "TWD",
            }
            
            query_string = urllib.parse.urlencode(params)
            target_url = f"{base_url}?{query_string}"
            
            print(f"[{i+1}/{total_days}] 正在搜尋日期: {checkin_str} (退房: {checkout_str})")
            
            page = context.new_page()
            final_count = "N/A"
            
            try:
                # 增加逾時設定並模擬人類行為
                page.goto(target_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(2000)

                # 定位數量資訊的各種可能選擇器 (Booking 常更換樣式)
                selectors = ["h1", "[data-testid='header-title']", ".ef29a7424c"]
                found_text = ""
                for selector in selectors:
                    element = page.query_selector(selector)
                    if element:
                        found_text = element.inner_text()
                        if "找到" in found_text or "properties found" in found_text:
                            break
                
                if found_text:
                    # 使用正則表達式擷取數字
                    match = re.search(r'([\d,]+)', found_text)
                    if match:
                        final_count = match.group(1)
                else:
                    # 備援方案：掃描全網頁文本
                    body_text = page.inner_text("body")
                    backup_match = re.search(r'找到\s*([\d,]+)\s*間住宿', body_text)
                    if backup_match:
                        final_count = backup_match.group(1)
                
                print(f"   -> 數量: {final_count}")
                
                # 存入結果清單
                results_list.append({
                    "搜尋日期": checkin_str,
                    "退房日期": checkout_str,
                    "地區": location,
                    "找到數量": final_count,
                    "搜尋連結": target_url
                })
                
            except Exception as e:
                print(f"   -> 搜尋 {checkin_str} 時發生錯誤: {e}")
            finally:
                page.close() 

        browser.close()

    # 匯出 Excel
    if results_list:
        df = pd.DataFrame(results_list)
        # 檔名加入日期範圍
        filename = f"booking_{location}_{start_date_str}_to_{end_date_str}.xlsx"
        df.to_excel(filename, index=False)
        print(f"\n[系統提示] 全數完成！資料已轉出至檔案: {filename}")
    else:
        print("\n[系統提示] 未抓取到任何有效資料。")

if __name__ == "__main__":
    print("=== Booking 逐日住宿數量查詢工具 (日期區間版) ===")
    input_location = input("1. 請輸入搜尋地區 (例如: 高雄): ")
    input_start_date = input("2. 請輸入入住起始日期 (格式: YYYY-MM-DD): ")
    input_end_date = input("3. 請輸入退房起始日期 (格式: YYYY-MM-DD): ")
    
    try:
        get_booking_count_per_day(input_location, input_start_date, input_end_date)
    except Exception as e:
        print(f"執行時發生錯誤: {e}")
    finally:
        input("\n按 Enter 鍵結束程式...")
