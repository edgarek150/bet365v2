import asyncio
import time

USERNAME = "Grzavr"
PASSWORD = "betuof"
EMAIL = "melancholera31@gmail.com"
DOB_DAY = "27"
DOB_MONTH = "jún"
DOB_YEAR = "1975"


async def login(page):
    """Full bet365 login: username/password modal + email/DOB verification iframe."""

    # Debug: print all buttons on the main page
    buttons = await page.query_selector_all("button")
    print(f"Found {len(buttons)} buttons on page:")
    for btn in buttons:
        label = await btn.get_attribute("aria-label")
        text = await btn.inner_text()
        print(f"  aria-label={repr(label)} text={repr(text)}")

    # Step 1: Click "Prihlásiť" to open the login modal
    try:
        await page.wait_for_selector("button:has-text('Prihlásiť')", timeout=10000)
        await page.click("button:has-text('Prihlásiť')")
        print("Clicked login button, waiting for modal...")
    except Exception as e:
        print(f"Login button not found: {e}")
        return False

    await asyncio.sleep(3)

    # Step 2: Fill username
    login_input = None
    for selector in [
        ".lms-StandardLogin_Username",
        "input[type='text']",
        "input[type='email']",
        "input[placeholder*='username' i]",
        "input[placeholder*='uživatel' i]",
        "input[name*='username']",
        "input[name*='user']",
        "input[name*='login']",
        "[class*='Username']",
        "[class*='username']",
    ]:
        login_input = await page.query_selector(selector)
        if login_input:
            print(f"Found username input with selector: {selector}")
            break
    if login_input:
        await login_input.fill(USERNAME)
        print("Filled username")
    else:
        print("No username input found")

    # Step 3: Fill password
    password_input = None
    for selector in [
        ".lms-StandardLogin_Password",
        "input[type='password']",
        "input[placeholder*='password' i]",
        "input[placeholder*='heslo' i]",
        "input[name*='password']",
        "input[name*='pass']",
        "[class*='Password']",
        "[class*='password']",
    ]:
        password_input = await page.query_selector(selector)
        if password_input:
            print(f"Found password input with selector: {selector}")
            break
    if password_input:
        await password_input.fill(PASSWORD)
        print("Filled password")
    else:
        print("No password input found")

    time.sleep(30)

    # Step 4: Click the LAST "Prihlásiť" button (submit inside modal)
    login_clicked = False
    for text in ["Prihlásiť", "Prihlásiť sa", "Přihlásit se", "Přihlásiť se", "Prihlásiť se"]:
        btns = await page.query_selector_all(f"button:has-text('{text}')")
        if btns:
            print(f"Found {len(btns)} buttons with text '{text}', clicking last one")
            await btns[-1].click()
            login_clicked = True
            print("Clicked submit button — LOGIN COMPLETED")
            break
    if not login_clicked:
        print("No submit button found")
        return False

    # Step 5: Handle email/DOB verification iframe (messageWindow)
    await asyncio.sleep(5)
    login_frame = page.frame(name="messageWindow")
    if login_frame:
        print("Found messageWindow iframe, filling verification form...")

        # Debug: print all options for each select
        for aria in ["Deň", "Mesiac", "Rok"]:
            opts = await login_frame.evaluate(f"""
                () => {{
                    const s = document.querySelector('select[aria-label="{aria}"]');
                    return s ? Array.from(s.options).map(o => o.value + ' | ' + o.text.trim()) : [];
                }}
            """)
            print(f"  {aria} options: {opts}")

        email_field = await login_frame.query_selector("#email")
        if email_field:
            await email_field.fill(EMAIL)
            await asyncio.sleep(2)
            await login_frame.select_option('select[aria-label="Deň"]', value=DOB_DAY)
            await asyncio.sleep(2)
            await login_frame.select_option('select[aria-label="Mesiac"]', value=DOB_MONTH)
            await asyncio.sleep(2)
            await login_frame.select_option('select[aria-label="Rok"]', value=DOB_YEAR)
            await asyncio.sleep(2)
            await login_frame.click("button:has-text('Prihlásiť sa')")
            await asyncio.sleep(5)
            print("Verification form submitted — LOGIN SUCCESSFUL")
        else:
            print("Email field not found in iframe")
            return False
    else:
        print("No messageWindow iframe found — skipping verification step")

    return True
