(() => {
  "use strict";
  const dataNode = document.getElementById("dashboard-data");
  let data;
  try { data = JSON.parse(dataNode.textContent || '{"sessions":[]}'); }
  catch (_) { data = { sessions: [] }; }
  const sessions = Array.isArray(data.sessions) ? data.sessions : [];
  let filtered = [...sessions];
  let selected = null;
  const $ = (id) => document.getElementById(id);
  const text = (value) => value == null ? "" : String(value);
  const element = (name, value) => { const node = document.createElement(name); if (value != null) node.textContent = text(value); return node; };
  const append = (parent, name, value) => { const node = element(name, value); parent.append(node); return node; };
  const hardwareName = (session) => text(session.hardware && session.hardware.cpu) || "unknown";
  const searchText = (session) => [session.id, session.status, session.backend, session.device, hardwareName(session)].map(text).join(" ").toLowerCase();
  const fillOptions = (id, key) => {
    const values = [...new Set(sessions.map((item) => item[key]).filter(Boolean))].sort();
    const select = $(id);
    values.forEach((value) => { const option = document.createElement("option"); option.value = text(value); option.textContent = text(value); select.append(option); });
  };
  const plot = (id, traces, layout) => { if (window.Plotly) window.Plotly.react(id, traces, Object.assign({paper_bgcolor:"transparent",plot_bgcolor:"transparent",font:{color:getComputedStyle(document.body).color}},layout || {}), {responsive:true}); };
  const renderRows = () => {
    const body = $("rows"); body.replaceChildren();
    filtered.forEach((session) => {
      const row = document.createElement("tr"); row.dataset.id = text(session.id);
      [session.id, session.status, session.backend, session.device, hardwareName(session), session.metrics && session.metrics.latency_mean_seconds != null ? session.metrics.latency_mean_seconds : "—"].forEach((value) => append(row, "td", value));
      row.addEventListener("click", () => show(session.id)); body.append(row);
    });
  };
  const renderCharts = () => {
    plot("history", [{x:filtered.map((s)=>s.created_at), y:filtered.map((s)=>Number((s.metrics||{}).latency_mean_seconds)||0), text:filtered.map((s)=>text(s.id)), mode:"markers", type:"scatter"}], {xaxis:{title:"Session time"},yaxis:{title:"Mean latency (s)"}});
    const groups = {}; filtered.forEach((s)=>{const key=hardwareName(s);groups[key]=(groups[key]||0)+1;});
    plot("hardware", [{x:Object.keys(groups),y:Object.values(groups),type:"bar"}], {yaxis:{title:"Sessions"}});
  };
  const draw = () => {
    const query = text($("search").value).toLowerCase();
    filtered = sessions.filter((session) => searchText(session).includes(query) && (!$('backend').value || session.backend === $('backend').value) && (!$('device').value || session.device === $('device').value) && (!$('status').value || session.status === $('status').value));
    $("count").textContent = `(${filtered.length})`; renderRows(); renderCharts();
  };
  const detailLine = (parent, label, value) => { const line = element("p"); const strong = append(line, "strong", `${label}: `); strong.textContent = `${label}: `; line.append(document.createTextNode(text(value))); parent.append(line); };
  const show = (id) => {
    selected = sessions.find((session) => session.id === id); if (!selected) return;
    const detail = $("detail"); detail.replaceChildren(); append(detail, "h2", "AI Assistant"); append(detail, "p", selected.assistant && selected.assistant.summary);
    const list = document.createElement("ul"); ((selected.assistant && selected.assistant.insights) || []).forEach((insight) => { const item = document.createElement("li"); append(item, "strong", `${text(insight.category)}: `); item.append(document.createTextNode(`${text(insight.summary)} ${text(insight.recommendation)}`)); list.append(item); }); detail.append(list);
    append(detail, "h2", "Report browser"); detailLine(detail, "Session", selected.id); const payload = element("pre", JSON.stringify(selected, null, 2)); detail.append(payload);
    const metrics = selected.metrics || {}; plot("comparison", [{x:Object.keys(metrics),y:Object.values(metrics).map(Number),type:"bar"}], {margin:{b:120}});
  };
  const csvField = (value) => `"${text(value).replaceAll('"','""')}"`;
  const download = (name, type, body) => { const anchor=document.createElement("a"); const url=URL.createObjectURL(new Blob([body],{type})); anchor.href=url; anchor.download=name; anchor.click(); URL.revokeObjectURL(url); };
  fillOptions("backend", "backend"); fillOptions("device", "device"); fillOptions("status", "status");
  $("export-json").addEventListener("click", () => download("aihw-bench-dashboard.json", "application/json", JSON.stringify(filtered,null,2)));
  $("export-csv").addEventListener("click", () => download("aihw-bench-dashboard.csv", "text/csv", [["id","status","backend","device","latency"], ...filtered.map((s)=>[s.id,s.status,s.backend,s.device,(s.metrics||{}).latency_mean_seconds])].map((row)=>row.map(csvField).join(",")).join("\n")));
  ["search","backend","device","status"].forEach((id)=>$(id).addEventListener("input",draw));
  $("theme").addEventListener("click",()=>{document.documentElement.dataset.theme=document.documentElement.dataset.theme === "dark" ? "light" : "dark"; draw(); if(selected) show(selected.id);}); draw();
})();
