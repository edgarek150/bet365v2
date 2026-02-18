import asyncio
import random
import datetime
from playwright.async_api import async_playwright

from login import login
from models import app_state, Link
from scraper import get_tourn_a_event, look_odds, accept_cookies, create_new_pairs
from processing.event_processor import initialize_urls
from utils.io import load_json_from_file
import config


async def open_new_tab(context, old_page, url):
    """Open url in a fresh tab and close the old one. Returns the new page."""
    new_page = await context.new_page()
    await new_page.goto(url, wait_until="domcontentloaded")
    await old_page.close()
    return new_page


async def is_logged_in(page) -> bool:
    """Return True if the account icon is present — user is already logged in."""
    try:
        el = await page.query_selector('[id="Icons-/-Account-/-Generic-Person---Reversed-Colours"]')
        return el is not None
    except Exception:
        return False


async def is_logged_out(page) -> bool:
    """Return True if the login button is visible — session has expired."""
    try:
        btn = await page.query_selector("button:has-text('Prihlásiť')")
        return btn is not None and await btn.is_visible()
    except Exception:
        return False


async def relogin_if_needed(context, page):
    """If the login button is detected, log an error and repeat the login flow. Returns current page."""
    if not await is_logged_out(page):
        return page
    from utils.logging import log_error
    log_error("Login button detected — session expired, re-logging in")
    print("⚠️  Session expired — re-logging in...")
    while True:
        try:
            success = await login(page)
            if success:
                print("✅ Re-login successful")
                page = await open_new_tab(context, page, config.SPORT_URLS[app_state.CURRENT_LANGUAGE])
                await asyncio.sleep(3)
                return page
            print("Re-login returned False, retrying in 10s...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Re-login error: {e}, retrying in 10s...")
            await asyncio.sleep(10)


async def reload_sport_page(context, page):
    """Open sport URL in a fresh tab, close the old one, verify still logged in. Returns new page."""
    page = await open_new_tab(context, page, config.SPORT_URLS[app_state.CURRENT_LANGUAGE])
    page = await relogin_if_needed(context, page)
    return page


def createPairsFromLinks(links):
    return [(link.tournament, link.event) for link in links]


def Compare_pairs(old_pairs, new_pairs):
    old_set = set(old_pairs)
    new_set = set(new_pairs)
    for old in old_set - new_set:
        for link in app_state.URLS:
            if link.tournament == old[0] and link.event == old[1]:
                app_state.URLS.remove(link)
                break
    return new_set - old_set


async def LoopNewUrl(context, page, in_pair, data):
    """Click a newly discovered event, open a fresh tab to scrape odds, return to sport in new tab."""
    print(f"New pair: {in_pair[0]} - {in_pair[1]}")
    sport_url = config.SPORT_URLS[app_state.CURRENT_LANGUAGE]
    try:
        # Fetch fresh element references from the current sport page each time,
        # because previous LoopNewUrl calls will have closed the old sport tab.
        tourn_texts, (event_texts, event_elements) = await get_tourn_a_event(page)  # noqa: elements used below
        fresh_pairs = create_new_pairs(tourn_texts, event_texts)
        index = fresh_pairs.index(in_pair)
        await event_elements[index].click()
        await asyncio.sleep(3)

        url = page.url
        new_link = Link(in_pair[0], in_pair[1], url, datetime.datetime.now())
        app_state.URLS.append(new_link)

        # Open event URL in a fresh tab, close the sport tab
        page = await open_new_tab(context, page, url)

        if in_pair[0] not in config.IGNORE_TOURN and not (
            in_pair[1] == "Handicaps" and config.IGNORE_HANDICAPS == 1
        ):
            await look_odds(page, data, new_link)

        # Return to sport page in a fresh tab, close event tab
        page = await open_new_tab(context, page, sport_url)
        await asyncio.sleep(2)

    except ValueError:
        print(f"Pair {in_pair} not found in fresh pairs list")
        page = await open_new_tab(context, page, sport_url)
        await asyncio.sleep(2)
    except Exception as e:
        print(f"LoopNewUrl error: {e}")
        page = await open_new_tab(context, page, sport_url)
        await asyncio.sleep(2)

    return page


async def Loop_URL(context, page, current_link: Link, data):
    """Open event URL in a fresh tab (closes sport tab), scrape odds, return page."""
    print(f"Looping URL: {current_link.tournament} - {current_link.event}")
    app_state.LOOPS_COUNTER += 1

    if current_link.event == "Handicaps" and app_state.LOOPS_COUNTER % 5 != 0:
        return page

    if current_link.tournament in config.IGNORE_TOURN:
        return page

    # Open event URL in a fresh tab, close the current (sport) tab
    page = await open_new_tab(context, page, current_link.url)
    await look_odds(page, data, current_link)

    sleep_time = random.randint(app_state.SEARCH_SLEEP[0], app_state.SEARCH_SLEEP[1])
    print(f"Sleeping {sleep_time}s after loop")
    await asyncio.sleep(sleep_time)

    return page


async def Main_Proccess(context, page, data):
    """Main scraping loop — finds new events and re-scrapes existing ones."""
    print("Main process started")
    while True:
        tourn_texts, (event_texts, _) = await get_tourn_a_event(page)

        if not tourn_texts:
            print("No tournaments found, reloading sport page...")
            page = await reload_sport_page(context, page)
            await asyncio.sleep(random.randint(app_state.LABEL_SLEEP[0], app_state.LABEL_SLEEP[1]))
            continue

        await accept_cookies(page)

        pairs = create_new_pairs(tourn_texts, event_texts)
        print(f"New pairs: {pairs}")

        known = createPairsFromLinks(app_state.URLS)
        new_pairs = sorted(Compare_pairs(known, pairs), key=lambda x: x[1])
        sorted_new = sorted(new_pairs, key=lambda x: (x[1] != "To Win Match", x))

        for pair in sorted_new:
            # Each call opens a new sport tab and closes the previous one, so
            # LoopNewUrl re-fetches elements fresh from the new tab.
            page = await LoopNewUrl(context, page, pair, data)

        # Re-scrape existing URLs, sorted by oldest timestamp first.
        # Each Loop_URL opens a fresh event tab (closes the current one).
        # After the loop, page is on the last event tab.
        app_state.URLS.sort(key=lambda x: (x.timestamp is None, x.timestamp))
        for link in list(app_state.URLS):
            if config.IGNORE_HANDICAPS == 1 and link.event == "Handicaps":
                continue
            if link.tournament in config.IGNORE_TOURN:
                continue
            page = await Loop_URL(context, page, link, data)

        # Open a fresh sport tab (closes the last event tab) and verify login.
        print(f"Cycle done at {datetime.datetime.now()}, reloading then sleeping...")
        page = await reload_sport_page(context, page)
        await asyncio.sleep(random.randint(app_state.LABEL_SLEEP[0], app_state.LABEL_SLEEP[1]))


async def Searching_Squash(context, page, data):
    """Wait for squash tournaments to appear, then start main process."""
    print("Searching for squash tournaments...")
    while True:
        tourn_texts, _ = await get_tourn_a_event(page)
        if tourn_texts:
            print(f"Found {len(tourn_texts)} tournaments, starting main process")
            await Main_Proccess(context, page, data)
            return
        else:
            print("No tournaments yet, reloading then retrying...")
            page = await reload_sport_page(context, page)
            await asyncio.sleep(random.randint(app_state.SEARCH_SLEEP[0], app_state.SEARCH_SLEEP[1]))


async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.bet365.com/", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        if await is_logged_in(page):
            print("Already logged in — skipping login")
        else:
            # --- Login loop ---
            while True:
                try:
                    success = await login(page)
                    if success:
                        break

                    print("Login returned False, retrying in 10s...")
                    await asyncio.sleep(10)
                except Exception as e:
                    print(f"Unexpected error during login: {e}, retrying in 10s...")
                    await asyncio.sleep(10)

        print("Login done — starting scraper")

        # Load persisted data and initialise known URLs
        data = load_json_from_file(config.DATA_JSON) or []
        initialize_urls(data)

        # Open sport page in a fresh tab, close the login tab
        page = await open_new_tab(context, page, config.SPORT_URLS[app_state.CURRENT_LANGUAGE])
        await asyncio.sleep(3)

        await accept_cookies(page)
        await Searching_Squash(context, page, data)


asyncio.run(scrape())
