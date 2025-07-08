from playwright.sync_api import sync_playwright

def get_session_storage_tokens(phone, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://eticket.railway.uz/uz/auth/login")
        page.fill('input[formcontrolname="phone"]', phone)
        page.fill('input[formcontrolname="password"]', password)

        page.wait_for_function("""
            () => {
                const el = document.querySelector('textarea[name="g-recaptcha-response"]');
                return el && el.value.trim().length > 0;
            }
        """)
        page.click('button[type="submit"]')
        page.wait_for_function("sessionStorage.getItem('token') !== null")
        session_token = page.evaluate("sessionStorage.getItem('token')")
        captcha_token = page.evaluate("sessionStorage.getItem('captcha')")
        user_json = page.evaluate("sessionStorage.getItem('user')")
        cookies = context.cookies()
        xsrf_token = next((c['value'] for c in cookies if c['name'] == 'XSRF-TOKEN'), None)
        
        browser.close()

        return session_token, captcha_token, user_json, xsrf_token, cookies

if __name__ == "__main__":
    phone = "+998882389003"
    password = "allamurod9003"

    print(get_session_storage_tokens(phone, password)[-2])
