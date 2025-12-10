from playwright.sync_api import Browser, expect


def test_budget_planning_flow(browser: Browser, base_url: str):

    context = browser.new_context(
        http_credentials={"username": "mc", "password": "MiniCyfr1!"}
    )
    page = context.new_page()
    # 1. Minister initial comment
    print("Step 1: Minister initial comment")
    # Login as Minister
    page.goto(f"{base_url}/")
    # Click the button inside the Minister card
    page.click("div.role-card:has-text('Ministerstwo') button")

    # Check status is "Planning Not Started"
    expect(page.locator("text=PLANOWANIE NIE ROZPOCZĘTE")).to_be_visible()

    # Click "Daj wytyczne"
    page.click("text=Daj wytyczne")

    # Fill comment and submit
    page.fill("#comment", "Proszę o oszczędne planowanie.")
    page.click("button[value='request_correction']")

    # Verify comment is visible
    expect(
        page.locator("text=Wysłano komentarz: Proszę o oszczędne planowanie.")
    ).to_be_visible()

    # 2. Chief starts planning
    print("Step 2: Chief starts planning")
    # Login as Chief
    page.goto(f"{base_url}/")
    page.click("div.role-card:has-text('Administracja') button")

    # Check status "Planning Not Started"
    expect(page.locator("text=PLANOWANIE NIE ROZPOCZĘTE")).to_be_visible()

    # Verify Minister's comment is visible
    expect(
        page.locator("text=Komentarz od Ministra: Proszę o oszczędne planowanie.")
    ).to_be_visible()

    # Set deadline and click "Start Planning"
    page.fill(".date-input", "2025-12-31")
    page.click("button[value='start']")

    # Verify status changes to "Planning In Progress"
    expect(page.locator("text=PLANOWANIE W TOKU")).to_be_visible()

    # 3. Office fills orders
    print("Step 3: Office fills orders")
    # Login as an Office (e.g., "Jednostka A")
    page.goto(f"{base_url}/")
    page.select_option("select[name='role']", "Jednostka A")
    page.click("div.role-card:has(select[name='role']) button")

    # Add 1st expense
    page.click("text=Dodaj nowy wydatek")

    # Wait for classification data to load
    page.wait_for_selector("#dzial option[value='750']", state="attached")

    page.select_option("#dzial", "750")
    page.select_option("#chapter", "75001")
    page.fill("#departament", "BA")
    page.fill("#task_name", "Zakup papieru")
    page.fill("#opis_projektu", "Papier do drukarek")
    page.fill("#termin_realizacji", "2026")
    page.fill("#budget_2025", "0")
    page.fill("#budget_2026", "100")
    page.fill("#budget_2027", "0")
    page.fill("#budget_2028", "0")
    page.fill("#budget_2029", "0")
    page.fill("#nr_umowy", "1/2026")
    page.click("button[type='submit']")

    # Add 2nd expense
    page.click("text=Dodaj nowy wydatek")
    page.select_option("#dzial", "750")
    page.select_option("#chapter", "75001")
    page.fill("#departament", "BA")
    page.fill("#task_name", "Zakup tonerów")
    page.fill("#opis_projektu", "Tonery do drukarek")
    page.fill("#termin_realizacji", "2026")
    page.fill("#budget_2025", "0")
    page.fill("#budget_2026", "200")
    page.fill("#budget_2027", "0")
    page.fill("#budget_2028", "0")
    page.fill("#budget_2029", "0")
    page.fill("#nr_umowy", "2/2026")
    page.click("button[type='submit']")

    # Verify expenses are listed
    expect(page.locator("text=Zakup papieru")).to_be_visible()
    expect(page.locator("text=Zakup tonerów")).to_be_visible()

    # Verify sum is correct (100 + 200 = 300)
    expect(page.locator("text=300 tys. zł")).to_be_visible()

    # Click "Submit for Acceptance"
    page.click("button:has-text('Wyślij do akceptacji')")

    # Verify status is "Submitted"
    expect(page.locator("text=Lista jest zamknięta")).to_be_visible()

    # 4. Chief submits for review
    print("Step 4: Chief submits for review")
    # Login as Chief
    page.goto(f"{base_url}/")
    page.click("div.role-card:has-text('Administracja') button")

    # Verify Office status is "Submitted"
    # We need to find the row for Jednostka A and check for "Zatwierdzony"
    row = page.locator("tr:has-text('Jednostka A')")
    expect(row.locator("text=Zatwierdzony")).to_be_visible()

    # Verify total sum
    expect(page.locator("text=300 tys. zł")).to_be_visible()

    # Click "Submit to Minister"
    page.click("button[value='submit_minister']")

    # Verify status is "In Review"
    expect(page.locator("text=W PRZEGLĄDZIE W MINISTERSTWIE")).to_be_visible()

    # 5. Minister requests correction
    print("Step 5: Minister requests correction")
    # Login as Minister
    page.goto(f"{base_url}/")
    page.click("div.role-card:has-text('Ministerstwo') button")

    # Verify status is "In Review"
    expect(page.locator("text=DO ZATWIERDZENIA")).to_be_visible()

    # Click "Request Correction"
    page.click("text=Zleć korektę")

    # Fill comment and submit
    page.fill("#comment", "Proszę zmniejszyć wydatki o 50 tys.")
    page.click("button[value='request_correction']")

    # Verify status is "Needs Correction"
    expect(page.locator("text=POTRZEBUJE KOREKTY")).to_be_visible()

    # 6. Chief restarts planning
    print("Step 6: Chief restarts planning")
    # Login as Chief
    page.goto(f"{base_url}/")
    page.click("div.role-card:has-text('Administracja') button")

    # Verify status is "Needs Correction"
    expect(page.locator("text=POTRZEBA KOREKTY")).to_be_visible()

    # Verify Minister's comment
    expect(
        page.locator("text=Komentarz od Ministra: Proszę zmniejszyć wydatki o 50 tys.")
    ).to_be_visible()

    # Set new deadline and click "Resume Planning"
    page.fill(".date-input", "2026-01-15")
    page.click("button[value='start']")

    # Verify status is "Planning In Progress"
    expect(page.locator("text=PLANOWANIE W TOKU")).to_be_visible()

    # 7. Office adds expense (or modifies, but let's add one more as per request "adds an expense")
    print("Step 7: Office adds expense")
    # Login as Office
    page.goto(f"{base_url}/")
    page.select_option("select[name='role']", "Jednostka A")
    page.click("div.role-card:has(select[name='role']) button")

    # Verify status allows editing
    expect(page.locator("text=Dodaj nowy wydatek")).to_be_visible()

    # Add another expense (maybe negative to simulate reduction, or just another one)
    # The prompt says "office adds an expense", let's add a small one.
    page.click("text=Dodaj nowy wydatek")
    page.select_option("#dzial", "750")
    page.select_option("#chapter", "75001")
    page.fill("#departament", "BA")
    page.fill("#task_name", "Długopisy")
    page.fill("#opis_projektu", "Długopisy")
    page.fill("#termin_realizacji", "2026")
    page.fill("#budget_2025", "0")
    page.fill("#budget_2026", "10")
    page.fill("#budget_2027", "0")
    page.fill("#budget_2028", "0")
    page.fill("#budget_2029", "0")
    page.fill("#nr_umowy", "3/2026")
    page.click("button[type='submit']")

    # Submit again
    page.click("button:has-text('Wyślij do akceptacji')")

    # 8. Chief submits for review again
    print("Step 8: Chief submits for review again")
    # Login as Chief
    page.goto(f"{base_url}/")
    page.click("div.role-card:has-text('Administracja') button")

    # Submit to Minister
    page.click("button[value='submit_minister']")

    # 9. Minister accepts
    print("Step 9: Minister accepts")
    # Login as Minister
    page.goto(f"{base_url}/")
    page.click("div.role-card:has-text('Ministerstwo') button")

    # Click "Approve"
    page.click("button[value='approve']")

    # Verify status is "Finished"
    expect(page.locator("text=PLANOWANIE ZAKOŃCZONE")).to_be_visible()
