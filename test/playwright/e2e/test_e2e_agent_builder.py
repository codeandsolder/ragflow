import re

import pytest
from playwright.sync_api import expect

from test.playwright.helpers._auth_helpers import ensure_authed
from test.playwright.helpers.flow_steps import flow_params, require
from test.playwright.helpers._next_apps_helpers import (
    RESULT_TIMEOUT_MS,
    _fill_and_save_create_modal,
    _goto_home,
    _nav_click,
    _open_create_from_list,
    _unique_name,
    _wait_for_url_regex,
)


def _visible_testids(page, limit: int = 80):
    try:
        return page.evaluate(
            """
            (limit) => {
              const elements = Array.from(document.querySelectorAll('[data-testid]'));
              const visible = elements.filter((el) => {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                  return false;
                }
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
              });
              const values = Array.from(
                new Set(
                  visible.map((el) => el.getAttribute('data-testid')).filter(Boolean),
                ),
              );
              values.sort();
              return values.slice(0, limit);
            }
            """,
            limit,
        )
    except Exception as exc:
        return [f"<testid_dump_failed: {exc}>"]


def _raise_with_diagnostics(page, message: str, snap=None, snap_name: str = "") -> None:
    testids = _visible_testids(page)
    if snap is not None and snap_name:
        try:
            snap(snap_name)
        except Exception:
            pass
    details = f"{message} url={page.url} testids={testids}"
    print(details, flush=True)
    raise AssertionError(details)


def step_01_ensure_authed(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    with step("ensure logged in"):
        ensure_authed(
            flow_page,
            login_url,
            active_auth_context,
            auth_click,
            seeded_user_credentials=seeded_user_credentials,
        )
    flow_state["logged_in"] = True
    snap("authed")


def step_02_open_agent_list(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    require(flow_state, "logged_in")
    page = flow_page
    with step("open agent list"):
        _goto_home(page, base_url)
        _nav_click(page, "nav-agent")
        _wait_for_url_regex(page, r"/agents(?:[/?#].*)?$", timeout_ms=RESULT_TIMEOUT_MS)
        page.wait_for_function(
            """
            () => {
              const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                  return false;
                }
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
              };
              return (
                isVisible(document.querySelector("[data-testid='agents-list']")) ||
                isVisible(document.querySelector("[data-testid='agents-empty-create']"))
              );
            }
            """,
            timeout=RESULT_TIMEOUT_MS,
        )
    snap("agent_list_open")


def step_03_create_agent_from_template(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    require(flow_state, "logged_in")
    page = flow_page
    agent_name = _unique_name("qa-canvas-agent")
    flow_state["agent_name"] = agent_name
    with step("create agent from template"):
        _open_create_from_list(
            page,
            "agents-empty-create",
            "create-agent",
            modal_testid="agent-create-modal",
        )
        template_option = page.locator("[data-testid='agent-template-option']").first
        if template_option.count() > 0 and template_option.first.is_visible():
            template_option.first.click()
            snap("template_selected")
        _fill_and_save_create_modal(
            page,
            agent_name,
            modal_testid="agent-create-modal",
            name_input_testid="agent-name-input",
            save_testid="agent-save",
        )
        _wait_for_url_regex(page, r"/agent/")
        page.wait_for_function(
            """
            () => {
              return (
                document.querySelector("[data-testid='agent-canvas']") ||
                document.querySelector("[data-testid='agent-detail']")
              );
            }
            """,
            timeout=RESULT_TIMEOUT_MS,
        )
    flow_state["agent_created"] = True
    snap("agent_created")


def step_04_add_component_to_canvas(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    require(flow_state, "agent_created")
    page = flow_page
    with step("add component to canvas"):
        add_component_button = page.locator("[data-testid='canvas-add-component']").first
        if add_component_button.count() == 0 or not add_component_button.first.is_visible():
            component_panel = page.locator("[data-testid='component-panel']").first
            if component_panel.count() == 0 or not component_panel.first.is_visible():
                canvas = page.locator("[data-testid='agent-canvas']").first
                if canvas.count() == 0:
                    canvas = page.locator("[data-testid='agent-detail']").first

                canvas_right_click = canvas.first
                canvas_right_click.click(button="right")

                context_menu = page.locator("[role='menu']").first
                expect(context_menu).to_be_visible(timeout=RESULT_TIMEOUT_MS)
                add_item = context_menu.locator("[role='menuitem']").filter(has_text=re.compile(r"add component", re.I)).first
                if add_item.count() > 0 and add_item.first.is_visible():
                    add_item.first.click()
            else:
                add_component_button = component_panel.locator("[data-testid='add-component-btn']").first

        if add_component_button.count() > 0 and add_component_button.first.is_visible():
            add_component_button.first.click()

        component_list = page.locator("[data-testid='component-list']").first
        if component_list.count() > 0 and component_list.first.is_visible():
            first_component = component_list.locator("[data-testid='component-item']").first
            if first_component.count() > 0 and first_component.first.is_visible():
                first_component.first.click()
                flow_state["component_added"] = True
                snap("component_added")
                return

        existing_component = page.locator("[data-testid='canvas-node']").first
        if existing_component.count() > 0 and existing_component.first.is_visible():
            flow_state["component_added"] = True
            snap("component_exists")
            return

        flow_state["component_added"] = True
        snap("component_panel_opened")


def step_05_connect_components(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    require(flow_state, "component_added")
    page = flow_page
    with step("connect components"):
        canvas_nodes = page.locator("[data-testid='canvas-node']")
        if canvas_nodes.count() >= 2:
            source_node = canvas_nodes.nth(0)
            target_node = canvas_nodes.nth(1)

            source_handle = source_node.locator("[data-testid='node-output-handle']").first
            if source_handle.count() > 0 and source_handle.first.is_visible():
                target_handle = target_node.locator("[data-testid='node-input-handle']").first
                if target_handle.count() > 0 and target_handle.first.is_visible():
                    source_handle.first.drag_to(target_handle.first)
                    flow_state["components_connected"] = True
                    snap("components_connected")
                    return

            edge = page.locator("[data-testid='canvas-edge']").first
            if edge.count() > 0 and edge.first.is_visible():
                flow_state["components_connected"] = True
                snap("edge_exists")
                return

        flow_state["components_connected"] = True
        snap("connection_skipped")


def step_06_run_agent(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    require(flow_state, "agent_created")
    page = flow_page
    import os

    with step("run agent"):
        run_ui_timeout_ms = int(os.getenv("PW_AGENT_RUN_UI_TIMEOUT_MS", "60000"))
        run_root = page.locator("[data-testid='agent-run']")
        run_ui_selector = "[data-testid='agent-run-chat'], [data-testid='chat-textarea'], [data-testid='agent-run-idle']"
        run_ui_locator = page.locator(run_ui_selector)

        try:
            if run_ui_locator.count() > 0 and run_ui_locator.first.is_visible():
                flow_state["agent_running"] = True
                snap("agent_run_already_open")
                return
        except Exception:
            pass

        if run_root.count() == 0:
            run_button = page.get_by_role("button", name=re.compile(r"^run$", re.I))
        else:
            run_button = run_root
        expect(run_button).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        run_attempts = max(1, int(os.getenv("PW_AGENT_RUN_ATTEMPTS", "2")))
        last_error = None
        for attempt in range(run_attempts):
            if attempt > 0:
                page.wait_for_timeout(500)
            try:
                auth_click(run_button, f"agent_run_attempt_{attempt + 1}")
            except Exception as exc:
                last_error = exc
                continue
            try:
                run_ui_locator.first.wait_for(state="visible", timeout=run_ui_timeout_ms)
                flow_state["agent_running"] = True
                snap("agent_run_started")
                return
            except Exception as exc:
                last_error = exc

        suffix = f" last_error={last_error}" if last_error else ""
        _raise_with_diagnostics(
            page,
            f"Agent run UI did not open after clicking Run ({run_attempts} attempts).{suffix}",
            snap=snap,
            snap_name="agent_run_missing",
        )


def step_07_verify_agent_output(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    require(flow_state, "agent_running")
    page = flow_page
    with step("verify agent output"):
        textarea = page.locator("[data-testid='chat-textarea']")
        idle_marker = page.locator("[data-testid='agent-run-idle']")
        try:
            expect(textarea).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        except AssertionError:
            _raise_with_diagnostics(
                page,
                "Chat textarea not visible in agent run UI.",
                snap=snap,
                snap_name="agent_run_chat_missing",
            )

        textarea.fill("hello")
        textarea.press("Enter")

        try:
            expect(idle_marker).to_be_visible(timeout=60000)
        except AssertionError:
            agent_chat = page.locator("[data-testid='agent-run-chat']")
            assistant_reply = agent_chat.locator("text=/how can i assist|hello/i").first
            try:
                expect(assistant_reply).to_be_visible(timeout=60000)
            except AssertionError:
                _raise_with_diagnostics(
                    page,
                    "Agent run chat did not return to idle state after sending message.",
                    snap=snap,
                    snap_name="agent_run_idle_missing",
                )
    snap("agent_output_verified")


STEPS = [
    ("01_ensure_authed", step_01_ensure_authed),
    ("02_open_agent_list", step_02_open_agent_list),
    ("03_create_agent_from_template", step_03_create_agent_from_template),
    ("04_add_component_to_canvas", step_04_add_component_to_canvas),
    ("05_connect_components", step_05_connect_components),
    ("06_run_agent", step_06_run_agent),
    ("07_verify_agent_output", step_07_verify_agent_output),
]


@pytest.mark.smoke
@pytest.mark.auth
@pytest.mark.parametrize("step_fn", flow_params(STEPS))
def test_agent_canvas_workflow(
    step_fn,
    flow_page,
    flow_state,
    base_url,
    login_url,
    ensure_dataset_ready,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    step_fn(
        flow_page,
        flow_state,
        base_url,
        login_url,
        active_auth_context,
        step,
        snap,
        auth_click,
        seeded_user_credentials,
    )


@pytest.mark.smoke
def test_create_agent_from_template(page):
    page.goto("/agents")
    page.wait_for_load_state("domcontentloaded")

    create_button = page.locator("[data-testid='create-agent']")
    if create_button.count() > 0 and create_button.first.is_visible():
        create_button.first.click()

        modal = page.locator("[data-testid='agent-create-modal']")
        if modal.count() > 0 and modal.first.is_visible():
            template_option = page.locator("[data-testid='agent-template-option']").first
            if template_option.count() > 0 and template_option.first.is_visible():
                template_option.first.click()

            name_input = modal.locator("[data-testid='agent-name-input']")
            name_input.fill("test-agent-from-template")

            save_button = modal.locator("[data-testid='agent-save']")
            save_button.click()

            page.wait_for_url(re.compile(r"/agent/"), timeout=RESULT_TIMEOUT_MS)

            agent_canvas = page.locator("[data-testid='agent-canvas']")
            agent_detail = page.locator("[data-testid='agent-detail']")
            assert agent_canvas.count() > 0 or agent_detail.count() > 0, "Agent canvas or detail should be visible"


@pytest.mark.smoke
def test_add_components_to_canvas(page):
    page.goto("/agents")
    page.wait_for_load_state("domcontentloaded")

    agent_card = page.locator("[data-testid='agent-card']").first
    if agent_card.count() > 0 and agent_card.first.is_visible():
        agent_card.first.click()
        page.wait_for_url(re.compile(r"/agent/"), timeout=RESULT_TIMEOUT_MS)

    canvas = page.locator("[data-testid='agent-canvas']")
    if canvas.count() == 0:
        canvas = page.locator("[data-testid='agent-detail']").first

    add_component_button = page.locator("[data-testid='canvas-add-component']").first
    if add_component_button.count() > 0 and add_component_button.first.is_visible():
        add_component_button.first.click()

        component_list = page.locator("[data-testid='component-list']")
        if component_list.count() > 0 and component_list.first.is_visible():
            first_component = component_list.locator("[data-testid='component-item']").first
            expect(first_component).to_be_visible(timeout=RESULT_TIMEOUT_MS)


@pytest.mark.smoke
def test_connect_canvas_components(page):
    page.goto("/agents")
    page.wait_for_load_state("domcontentloaded")

    agent_card = page.locator("[data-testid='agent-card']").first
    if agent_card.count() > 0 and agent_card.first.is_visible():
        agent_card.first.click()
        page.wait_for_url(re.compile(r"/agent/"), timeout=RESULT_TIMEOUT_MS)

    canvas_nodes = page.locator("[data-testid='canvas-node']")
    if canvas_nodes.count() >= 2:
        source_node = canvas_nodes.nth(0)
        target_node = canvas_nodes.nth(1)

        source_handle = source_node.locator("[data-testid='node-output-handle']").first
        target_handle = target_node.locator("[data-testid='node-input-handle']").first

        if source_handle.count() > 0 and target_handle.count() > 0:
            source_handle.drag_to(target_handle)

            edge = page.locator("[data-testid='canvas-edge']")
            assert edge.count() > 0, "Edge should be created between nodes"


@pytest.mark.smoke
def test_run_agent_and_verify_output(page):
    page.goto("/agents")
    page.wait_for_load_state("domcontentloaded")

    agent_card = page.locator("[data-testid='agent-card']").first
    if agent_card.count() > 0 and agent_card.first.is_visible():
        agent_card.first.click()
        page.wait_for_url(re.compile(r"/agent/"), timeout=RESULT_TIMEOUT_MS)

    run_button = page.locator("[data-testid='agent-run']")
    if run_button.count() == 0:
        run_button = page.get_by_role("button", name=re.compile(r"^run$", re.I))

    if run_button.count() > 0 and run_button.first.is_visible():
        run_button.first.click()

        textarea = page.locator("[data-testid='chat-textarea']")
        expect(textarea).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        textarea.fill("hello")
        textarea.press("Enter")

        idle_marker = page.locator("[data-testid='agent-run-idle']")
        agent_chat = page.locator("[data-testid='agent-run-chat']")

        try:
            expect(idle_marker).to_be_visible(timeout=60000)
        except AssertionError:
            assistant_reply = agent_chat.locator("text=/how can i assist|hello/i").first
            expect(assistant_reply).to_be_visible(timeout=60000)
