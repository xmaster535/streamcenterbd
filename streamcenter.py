import asyncio
from datetime import timedelta
from functools import partial
import json
from selectolax.parser import HTMLParser
from utils import Cache, Time, get_logger, leagues, network

log = get_logger(__name__)
TAG = "STRMCNTR"
CACHE_FILE = Cache(TAG, exp=86_400)
API_URL = "https://backend.streamcenter.live/api/Parties"

# প্রতিটি ইভেন্টের জন্য নির্ধারিত লোগো লিঙ্ক
DEFAULT_EVENT_LOGO = "https://i.ibb.co.com/Z1YSQKbc/Chat-GPT-Image-May-9-2026-01-31-16-AM.png"

CATEGORIES = {
    4: "Basketball",
    9: "Football",
    13: "Baseball",
    15: "Motor Sport",
    16: "Hockey",
    17: "Fight MMA",
    18: "Boxing",
    20: "WWE",
    21: "Tennis",
}

async def process_event(url: str, url_num: int) -> str | None:
    if not (html_data := await network.request(url, log=log)):
        return None
    soup = HTMLParser(html_data.content)
    iframe = soup.css_first("iframe")
    if not iframe or not (iframe_src := iframe.attributes.get("src")):
        return None
    
    m3u8_id = iframe_src.rsplit('=', 1)[-1]
    # হেডার ফরম্যাট অনুযায়ী লিঙ্ক তৈরি
    headers = "|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0&Referer=https://streamcenter.xyz&Origin=https://streamcenter.xyz"
    return f"https://mainstreams.pro/hls/{m3u8_id}.m3u8{headers}"

async def get_events() -> list[dict]:
    events = []
    if not (r := await network.request(API_URL, params={"pageNumber": 1, "pageSize": 500}, log=log)):
        return events
    api_data = r.json()
    
    for stream_group in api_data:
        category_id = stream_group.get("categoryId")
        name = stream_group.get("gameName", " ")
        iframe = stream_group.get("videoUrl")
        event_time_str = stream_group.get("beginPartie")
        if not (category_id and iframe and event_time_str): continue
        
        event_dt = Time.from_str(event_time_str)
        if not (sport := CATEGORIES.get(category_id)): continue

        # ইভেন্ট শেষ হওয়ার সময় হিসেব করা
        end_dt = event_dt + timedelta(hours=3)

        # টিম এ এবং টিম বি আলাদা করার চেষ্টা
        teams = name.split(" vs ") if " vs " in name else [name, " "]
        teamA = teams[0]
        teamB = teams[1] if len(teams) > 1 else " "

        events.append({
            "sport": sport,
            "eventName": name,
            "teamAName": teamA,
            "teamBName": teamB,
            "link": iframe.split("<")[0],
            "start_date": event_dt.strftime("%Y-%m-%d"),
            "start_time": event_dt.strftime("%H:%M"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "end_time": end_dt.strftime("%H:%M")
        })
    return events

async def scrape() -> None:
    log.info('Scraping started for new JSON format with Start/End times and default logo...')
    events = await get_events()
    final_output = []

    if events:
        for i, ev in enumerate(events, start=1):
            stream_url = await process_event(ev["link"], i)
            if not stream_url: continue

            # আপডেট করা JSON স্ট্রাকচার
            entry = {
                "category": ev["sport"],
                "categoryLogo": "",
                "date": ev["start_date"],
                "time": ev["start_time"],
                "end_date": ev["end_date"],
                "end_time": ev["end_time"],
                "eventLogo": DEFAULT_EVENT_LOGO,
                "eventName": ev["eventName"],
                "link_names": ["DlSports"],
                "show_noti": False,
                "streaming_links": [
                    {
                        "api": "",
                        "link": stream_url,
                        "name": "DlSports",
                        "tokenApi": ""
                    }
                ],
                "teamAFlag": " ",
                "teamAName": ev["teamAName"],
                "teamBFlag": " ",
                "teamBName": ev["teamBName"],
                "visible": True
            }
            final_output.append(entry)
            log.info(f"URL {i}) Processed: {ev['eventName']} [{ev['start_time']} - {ev['end_time']}]")

    # ফাইল ওপেন ও সেভ করার লাইনের ইনডেন্টেশন ঠিক করা হয়েছে
    with open("strmcntr_cache.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
    log.info(f"Saved {len(final_output)} events to strmcntr_cache.json")
