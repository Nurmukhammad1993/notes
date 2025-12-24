(() => {
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function getTheme() {
    const stored = (() => {
      try {
        return localStorage.getItem("theme");
      } catch {
        return null;
      }
    })();
    if (stored === "dark" || stored === "light") return stored;
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    return prefersDark ? "dark" : "light";
  }

  function setTheme(theme) {
    const isDark = theme === "dark";
    document.documentElement.classList.toggle("dark", isDark);
    try {
      localStorage.setItem("theme", theme);
    } catch {}
    const btn = qs("#theme-toggle");
    const label = qs("#theme-toggle-label");
    if (label) label.textContent = isDark ? "Тёмная" : "Светлая";
    if (btn) {
      const sun = qs("[data-theme-icon='sun']", btn);
      const moon = qs("[data-theme-icon='moon']", btn);
      if (sun) sun.classList.toggle("hidden", !isDark);
      if (moon) moon.classList.toggle("hidden", isDark);
      btn.setAttribute("aria-label", isDark ? "Тема: тёмная" : "Тема: светлая");
    }
  }

  function initThemeToggle() {
    const btn = qs("#theme-toggle");
    if (!btn) return;
    setTheme(getTheme());
    btn.addEventListener("click", () => {
      const next = document.documentElement.classList.contains("dark") ? "light" : "dark";
      setTheme(next);
    });
  }

  function autosize(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  }

  function initAutosize() {
    qsa("textarea[data-autosize='1']").forEach((ta) => {
      const handler = () => autosize(ta);
      ta.addEventListener("input", handler);
      // Initial
      handler();
    });
  }

  function initCtrlEnterSubmit() {
    qsa("form[data-ctrl-enter-submit='1']").forEach((form) => {
      form.addEventListener("keydown", (e) => {
        const isCtrlEnter = (e.ctrlKey || e.metaKey) && e.key === "Enter";
        if (!isCtrlEnter) return;
        const tag = (e.target && e.target.tagName) || "";
        if (tag !== "TEXTAREA" && tag !== "INPUT") return;
        e.preventDefault();
        const submit = qs("button[type='submit']", form);
        if (submit) submit.click();
        else form.requestSubmit?.();
      });
    });
  }

  function toast(message, tone = "info") {
    const host = qs("#toast-host");
    if (!host) return;

    const el = document.createElement("div");
    const toneClasses = {
      info: "border-slate-200 bg-white/80 text-slate-900 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100",
      success:
        "border-emerald-200 bg-emerald-50/80 text-emerald-900 dark:border-emerald-700/60 dark:bg-emerald-950/40 dark:text-emerald-50",
      danger:
        "border-rose-200 bg-rose-50/80 text-rose-900 dark:border-rose-700/60 dark:bg-rose-950/40 dark:text-rose-50",
    };

    el.className = `pointer-events-auto w-full max-w-sm rounded-2xl border px-4 py-3 shadow-sm backdrop-blur ${toneClasses[tone] || toneClasses.info}`;
    el.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="mt-0.5 h-2.5 w-2.5 rounded-full ${
          tone === "success" ? "bg-emerald-400" : tone === "danger" ? "bg-rose-400" : "bg-indigo-400"
        }"></div>
        <div class="flex-1">
          <div class="text-sm font-medium">${message}</div>
          <div class="mt-0.5 text-xs opacity-80">Ctrl+Enter — быстрое сохранение</div>
        </div>
        <button aria-label="Close" class="rounded-lg px-2 py-1 text-xs opacity-80 hover:opacity-100">Esc</button>
      </div>
    `;

    const closeBtn = qs("button", el);
    const remove = () => {
      el.classList.add("opacity-0", "translate-y-2");
      setTimeout(() => el.remove(), 180);
    };

    closeBtn.addEventListener("click", remove);
    const esc = (e) => {
      if (e.key !== "Escape") return;
      remove();
      window.removeEventListener("keydown", esc);
    };
    window.addEventListener("keydown", esc);

    el.classList.add("transition", "duration-200", "ease-out");
    host.appendChild(el);

    setTimeout(remove, 3500);
  }

  function initToastsFromQuery() {
    const params = new URLSearchParams(window.location.search);
    if (params.get("created") === "1") toast("Заметка создана", "success");
    if (params.get("updated") === "1") toast("Заметка обновлена", "success");
    if (params.get("deleted") === "1") toast("Заметка удалена", "danger");

    if (params.has("created") || params.has("updated") || params.has("deleted")) {
      // Clean URL without reloading
      const url = new URL(window.location.href);
      url.searchParams.delete("created");
      url.searchParams.delete("updated");
      url.searchParams.delete("deleted");
      window.history.replaceState({}, "", url);
    }
  }

  function initLocalTime() {
    qsa("time[data-utc]").forEach((t) => {
      const raw = t.getAttribute("data-utc");
      if (!raw) return;
      const d = new Date(raw);
      if (Number.isNaN(d.getTime())) return;
      t.textContent = d.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
      t.setAttribute("title", raw);
    });
  }

  async function writeClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    // Fallback
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }

  function initCopyButtons() {
    qsa("button[data-copy-payload]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          const payload = JSON.parse(btn.getAttribute("data-copy-payload") || "{}");
          const title = (payload.title || "").toString().trim();
          const content = (payload.content || "").toString();
          const text = content ? `${title}\n\n${content}` : title;
          await writeClipboard(text);
          toast("Скопировано в буфер", "success");
        } catch (e) {
          toast("Не удалось скопировать", "danger");
        }
      });
    });
  }

  function initClearNewNote() {
    const btn = qs("button[data-clear-new-note='1']");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const title = qs("#new-note-title");
      const content = qs("#new-note-content");
      if (title) title.value = "";
      if (content) {
        content.value = "";
        autosize(content);
      }
      title?.focus?.();
      toast("Форма очищена", "info");
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initThemeToggle();
    initAutosize();
    initCtrlEnterSubmit();
    initToastsFromQuery();
    initLocalTime();
    initCopyButtons();
    initClearNewNote();
  });
})();
