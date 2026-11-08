/**
 * Tebar Dashboard Plugin
 *
 * Plain IIFE using the Hermes Plugin SDK globals. No build step, no imports.
 * Renders: status card, connected accounts, posts list, composer.
 */
(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const {
    Card, CardHeader, CardTitle, CardContent,
    Badge, Button, Input, Label, Separator,
  } = SDK.components;
  const { useState, useEffect, useCallback } = SDK.hooks;
  const { cn, isoTimeAgo } = SDK.utils;

  const API = "/api/plugins/tebar";

  const STATUS_TONE = {
    published: "success",
    scheduled: "info",
    failed: "error",
    draft: "warning",
  };

  function useTebar(url, deps) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const load = useCallback(function () {
      setLoading(true);
      setError(null);
      SDK.fetchJSON(url)
        .then(setData)
        .catch(function (err) {
          setError(err && err.message ? err.message : String(err));
          setData(null);
        })
        .finally(function () { setLoading(false); });
    }, [url]);

    useEffect(function () {
      load();
    }, [load]);

    return { data, loading, error, reload: load };
  }

  function AccountAvatar({ account }) {
    const src = account.avatar || account.avatar_url;
    const name = account.name || account.handle || account.platform || "account";
    if (src) {
      return React.createElement("img", {
        src: src,
        alt: name,
        className: "h-8 w-8 rounded-full object-cover shrink-0 border border-border",
      });
    }
    const initial = (String(name).slice(0, 1) || "?").toUpperCase();
    return React.createElement("div", {
      className: "h-8 w-8 rounded-full bg-background/40 border border-border shrink-0 flex items-center justify-center font-courier text-sm",
    }, initial);
  }

  function StatusCard() {
    const s = useTebar(API + "/status", []);
    const d = s.data;
    return React.createElement(Card, null,
      React.createElement(CardHeader, null,
        React.createElement("div", { className: "flex items-center justify-between" },
          React.createElement(CardTitle, { className: "text-base" }, "Status"),
          React.createElement(Button, {
            onClick: s.reload,
            disabled: s.loading,
            className: cn(
              "inline-flex items-center gap-2 border border-border bg-background/40 px-3 py-1.5",
              "text-xs font-courier transition-colors hover:bg-foreground/10 cursor-pointer",
            ),
          }, s.loading ? "Refreshing..." : "Refresh"),
        ),
      ),
      React.createElement(CardContent, null,
        !d
          ? React.createElement("p", { className: "text-sm text-muted-foreground" },
              s.error || "Loading...")
          : React.createElement("div", { className: "flex flex-col gap-2 text-sm" },
            React.createElement("div", { className: "flex items-center gap-2" },
              React.createElement(Badge, { variant: "outline" }, d.configured ? "configured" : "not configured"),
              d.profile_id
                ? React.createElement(Badge, { variant: "outline" }, "profile " + d.profile_id)
                : null,
            ),
            d.configured
              ? React.createElement("div", { className: "text-muted-foreground" },
                  "Account: ",
                  React.createElement("span", { className: "font-courier text-foreground" },
                    (d.me && (d.me.email || d.me.name || d.me.handle || d.me.id)) || "unknown"),
                )
              : React.createElement("p", { className: "text-muted-foreground" },
                  "TEBAR_API_KEY belum diset — tambahkan di data/.env"),
            d.error && d.configured
              ? React.createElement("p", { className: "text-xs text-muted-foreground" }, "best-effort: " + d.error)
              : null,
          ),
      ),
    );
  }

  function AccountsCard() {
    const s = useTebar(API + "/accounts?limit=50", []);
    const d = s.data;
    const accounts = (d && d.data) || [];
    return React.createElement(Card, null,
      React.createElement(CardHeader, null,
        React.createElement(CardTitle, { className: "text-base" },
          "Connected accounts " + (accounts.length ? "(" + accounts.length + ")" : "")),
      ),
      React.createElement(CardContent, null,
        !d
          ? React.createElement("p", { className: "text-sm text-muted-foreground" },
              s.loading ? "Loading..." : (s.error || "No data"))
          : accounts.length === 0
            ? React.createElement("p", { className: "text-sm text-muted-foreground" },
                d.configured ? "No accounts connected." : "Set TEBAR_API_KEY to load accounts.")
            : React.createElement("div", { className: "grid gap-3" },
                accounts.map(function (a, i) {
                  const label = a.name || a.handle || a.platform || ("account " + (a.id || i));
                  const limit = a.publishing_limit;
                  return React.createElement("div", {
                    key: a.id || i,
                    className: "flex items-center gap-3 border border-border p-3",
                  },
                    React.createElement(AccountAvatar, { account: a }),
                    React.createElement("div", { className: "flex flex-col min-w-0" },
                      React.createElement("span", { className: "font-medium truncate" }, label),
                      React.createElement("span", { className: "text-xs text-muted-foreground" },
                        [a.platform, a.handle].filter(Boolean).join(" · ")),
                      limit !== null && limit !== undefined
                        ? React.createElement("span", { className: "text-xs text-muted-foreground font-courier" },
                            "publishing limit: " + (typeof limit === "object" ? (limit.limit ?? limit.value ?? JSON.stringify(limit)) : limit))
                        : null,
                    ),
                  );
                }),
              ),
      ),
    );
  }

  function StatusBadge({ status }) {
    const s = String(status || "unknown");
    return React.createElement("span", {
      className: cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-courier border border-border bg-background/40",
        STATUS_TONE[s] === "success" && "text-green-600",
        STATUS_TONE[s] === "info" && "text-blue-600",
        STATUS_TONE[s] === "error" && "text-red-600",
        STATUS_TONE[s] === "warning" && "text-amber-600",
      ),
    }, s);
  }

  function PostsCard() {
    const s = useTebar(API + "/posts?limit=20", []);
    const d = s.data;
    const posts = (d && d.data) || [];
    return React.createElement(Card, null,
      React.createElement(CardHeader, null,
        React.createElement(CardTitle, { className: "text-base" }, "Posts"),
      ),
      React.createElement(CardContent, null,
        !d
          ? React.createElement("p", { className: "text-sm text-muted-foreground" },
              s.loading ? "Loading..." : (s.error || "No data"))
          : posts.length === 0
            ? React.createElement("p", { className: "text-sm text-muted-foreground" }, "No posts yet.")
            : React.createElement("div", { className: "flex flex-col gap-3" },
                posts.map(function (p, i) {
                  const targets = p.targets || [];
                  return React.createElement("div", {
                    key: p.id || i,
                    className: "flex flex-col gap-1 border border-border p-3",
                  },
                    React.createElement("div", { className: "flex items-center gap-2" },
                      React.createElement(StatusBadge, { status: p.status }),
                      p.scheduled_at
                        ? React.createElement("span", { className: "text-xs text-muted-foreground font-courier" },
                            "scheduled " + isoTimeAgo(p.scheduled_at))
                        : null,
                    ),
                    React.createElement("p", { className: "text-sm truncate" },
                      (p.content || "").slice(0, 120) || "(no content)"),
                    targets.length
                      ? React.createElement("div", { className: "flex flex-wrap gap-1" },
                          targets.map(function (t, j) {
                            return React.createElement(Badge, { key: j, variant: "outline" },
                              (t.account_id || t.account_name || String(t)));
                          }))
                      : null,
                  );
                }),
              ),
      ),
    );
  }

  function Composer({ accounts, onCreated }) {
    const [content, setContent] = useState("");
    const [selected, setSelected] = useState([]);
    const [scheduledAt, setScheduledAt] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null); // {ok, message}

    const accountIds = accounts.map(function (a) { return a.id; });

    function toggle(id) {
      setSelected(function (prev) {
        return prev.indexOf(id) === -1 ? prev.concat(id) : prev.filter(function (x) { return x !== id; });
      });
    }

    function submit() {
      setSubmitting(true);
      setResult(null);
      SDK.fetchJSON(API + "/posts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: content,
          account_ids: selected,
          scheduled_at: scheduledAt || null,
        }),
      }).then(function (created) {
        setResult({ ok: true, message: "Post created" + (created && created.id ? " (" + created.id + ")" : "") + "." });
        setContent("");
        setSelected([]);
        setScheduledAt("");
        if (onCreated) onCreated();
      }).catch(function (err) {
        const detail = err && err.detail ? err.detail : (err && err.message ? err.message : String(err));
        setResult({ ok: false, message: String(detail) });
      }).finally(function () { setSubmitting(false); });
    }

    return React.createElement(Card, null,
      React.createElement(CardHeader, null,
        React.createElement(CardTitle, { className: "text-base" }, "New post"),
      ),
      React.createElement(CardContent, { className: "flex flex-col gap-4" },
        React.createElement("div", { className: "flex flex-col gap-1.5" },
          React.createElement(Label, { className: "text-sm font-medium" }, "Content"),
          React.createElement("textarea", {
            value: content,
            onChange: function (e) { setContent(e.target.value); },
            rows: 3,
            placeholder: "Write something...",
            className: cn("border border-border bg-background/40 p-2 rounded text-sm w-full",
              "font-courier focus:outline-none focus:border-foreground/40"),
          }),
        ),
        React.createElement("div", { className: "flex flex-col gap-1.5" },
          React.createElement(Label, { className: "text-sm font-medium" }, "Accounts"),
          accounts.length === 0
            ? React.createElement("p", { className: "text-xs text-muted-foreground" }, "No accounts available.")
            : React.createElement("div", { className: "flex flex-wrap gap-2" },
                accounts.map(function (a) {
                  const id = a.id;
                  const on = selected.indexOf(id) !== -1;
                  const label = a.name || a.handle || a.platform || id;
                  return React.createElement("button", {
                    key: id,
                    type: "button",
                    onClick: function () { toggle(id); },
                    className: cn(
                      "inline-flex items-center gap-1.5 border px-2.5 py-1 rounded text-xs font-courier cursor-pointer transition-colors",
                      on ? "border-foreground/50 bg-foreground/10" : "border-border bg-background/40 hover:bg-foreground/5",
                    ),
                  }, label);
                }),
              ),
        ),
        React.createElement("div", { className: "flex flex-col gap-1.5" },
          React.createElement(Label, { className: "text-sm font-medium" }, "Schedule (optional)"),
          React.createElement(Input, {
            type: "datetime-local",
            value: scheduledAt,
            onChange: function (e) { setScheduledAt(e.target.value); },
            className: "text-sm font-courier",
          }),
        ),
        React.createElement(Button, {
          onClick: submit,
          disabled: submitting || !content.trim() || selected.length === 0,
          className: cn(
            "inline-flex items-center justify-center gap-2 border border-border bg-background/40 px-4 py-2",
            "text-sm font-courier transition-colors hover:bg-foreground/10 cursor-pointer",
            "disabled:opacity-40 disabled:cursor-not-allowed",
          ),
        }, submitting ? "Creating..." : "Create post"),
        result
          ? React.createElement("p", {
              className: cn("text-sm font-courier", result.ok ? "text-green-600" : "text-red-600"),
            }, result.message)
          : null,
      ),
    );
  }

  function TebarPage() {
    const status = useTebar(API + "/status", []);
    const accounts = useTebar(API + "/accounts?limit=50", []);
    const posts = useTebar(API + "/posts?limit=20", []);
    const accountList = (accounts.data && accounts.data.data) || [];

    return React.createElement("div", { className: "flex flex-col gap-6" },
      React.createElement("div", { className: "flex items-center gap-3" },
        React.createElement(CardTitle, { className: "text-xl" }, "Tebar"),
        React.createElement(Badge, { variant: "outline" }, "v0.1.0"),
      ),
      React.createElement(StatusCard, null),
      React.createElement(AccountsCard, null),
      React.createElement(PostsCard, null),
      React.createElement(Composer, {
        accounts: accountList,
        onCreated: function () {
          accounts.reload();
          posts.reload();
        },
      }),
    );
  }

  window.__HERMES_PLUGINS__.register("tebar", TebarPage);
})();
