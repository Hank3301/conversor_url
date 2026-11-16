const $ = (id) => document.getElementById(id);

// Vazio = mesmo domínio (padrão). Se o frontend ficar em outro host
// (ex.: Cloudflare Pages), injete window.__API_BASE__ antes deste script.
const API_BASE = window.__API_BASE__ || "";

const form = $("form");
const urlInput = $("url");
const analyzeBtn = $("analyze");
const result = $("result");
const progressBox = $("progress");
const barFill = $("bar-fill");
const pTitle = $("p-title");
const pStatus = $("p-status");
const saveLink = $("save");
const cancelBtn = $("cancel");

let current = null; // { url, title }
let source = null; // EventSource
let activeJob = null;

function toast(message) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = message;
  $("toasts").appendChild(el);
  setTimeout(() => el.remove(), 6000);
}

async function api(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Falha na requisição.");
  return data;
}

function seconds(total) {
  if (!total) return "";
  const m = Math.floor(total / 60);
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function formatBytes(bytes) {
  if (!bytes) return "";
  const mb = bytes / (1024 * 1024);
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb.toFixed(1)} MB`;
}

function reset() {
  if (source) source.close();
  source = null;
  activeJob = null;
  progressBox.hidden = true;
  saveLink.hidden = true;
  barFill.style.width = "0";
  barFill.classList.remove("indeterminate");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  reset();
  result.hidden = true;
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analisando…";

  try {
    const info = await api("/api/resolve", { url });
    current = { url: info.url, title: info.title };

    $("title").textContent = info.title;
    const bits = [info.uploader, seconds(info.duration)].filter(Boolean);
    $("byline").textContent = bits.join(" · ") || "pronto para baixar";

    const thumb = $("thumb");
    if (info.thumbnail) {
      thumb.src = info.thumbnail;
      thumb.hidden = false;
    } else {
      thumb.hidden = true;
    }

    const video = $("video-chips");
    video.innerHTML = "";
    if (info.heights.length) {
      for (const h of info.heights) {
        video.appendChild(chip(`${h}p`, "video", { height: h }));
      }
    } else {
      video.innerHTML = '<span class="byline">sem vídeo disponível</span>';
    }

    const audio = $("audio-chips");
    audio.innerHTML = "";
    for (const kbps of info.bitrates) {
      audio.appendChild(chip(`${kbps} kbps`, "audio", { bitrate: kbps }));
    }

    $("limits").textContent =
      `Limites: até ${info.limits.max_duration_minutes} min e ` +
      `${info.limits.max_filesize_mb} MB por arquivo.`;
    $("max-min").textContent = info.limits.max_duration_minutes;
    $("max-mb").textContent = info.limits.max_filesize_mb;

    result.hidden = false;
  } catch (error) {
    toast(error.message);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analisar";
  }
});

function chip(label, kind, extra) {
  const el = document.createElement("button");
  el.type = "button";
  el.className = `chip ${kind}`;
  el.textContent = label;
  el.addEventListener("click", () => startDownload(kind, extra));
  return el;
}

async function startDownload(kind, extra) {
  if (!current) return;
  reset();
  result.hidden = true;

  progressBox.hidden = false;
  pTitle.textContent = current.title;
  pStatus.textContent = "Preparando no servidor…";
  barFill.style.width = "4%";

  try {
    const job = await api("/api/download", { url: current.url, kind, ...extra });
    activeJob = job.job_id;
    listen(job.job_id);
  } catch (error) {
    pStatus.textContent = error.message;
    toast(error.message);
  }
}

function listen(jobId) {
  source = new EventSource(`${API_BASE}/api/jobs/${jobId}/events`);

  source.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.status === "downloading") {
      if (typeof data.progress === "number" && data.progress > 0.03) {
        barFill.classList.remove("indeterminate");
        barFill.style.width = `${Math.round(data.progress * 100)}%`;
        pStatus.textContent = `Baixando… ${Math.round(data.progress * 100)}%`;
      } else {
        barFill.classList.add("indeterminate");
        pStatus.textContent = "Preparando o link…";
      }
    } else if (data.status === "processing") {
      barFill.classList.remove("indeterminate");
      barFill.style.width = "99%";
      pStatus.textContent = "Convertendo o arquivo…";
    } else if (data.status === "ready") {
      finish(jobId, data);
    } else if (data.status === "error") {
      barFill.classList.remove("indeterminate");
      pStatus.textContent = data.error || "Falhou.";
      toast(data.error || "Falhou.");
      stop();
    } else if (data.status === "canceled") {
      pStatus.textContent = "Cancelado.";
      stop();
    }
  };

  source.onerror = () => {
    if (source && source.readyState === EventSource.CLOSED) {
      pStatus.textContent = "Conexão encerrada.";
    }
  };
}

function finish(jobId, data) {
  stop();
  barFill.classList.remove("indeterminate");
  barFill.style.width = "100%";

  const size = formatBytes(data.size);
  pStatus.textContent = size ? `Pronto (${size}).` : "Pronto.";
  saveLink.href = `${API_BASE}/api/jobs/${jobId}/file`;
  saveLink.download = data.filename || "download";
  saveLink.hidden = false;
  saveLink.textContent = size ? `Baixar arquivo (${size})` : "Baixar arquivo";
  saveLink.click();
}

function stop() {
  if (source) source.close();
  source = null;
}

cancelBtn.addEventListener("click", async () => {
  if (!activeJob) return;
  stop();
  try {
    await api(`/api/jobs/${activeJob}/cancel`, {});
  } catch {
    /* ignora */
  }
  pStatus.textContent = "Cancelado.";
  barFill.classList.remove("indeterminate");
  barFill.style.width = "0";
});

urlInput.addEventListener("input", () => {
  if (result.hidden === false && current) return;
});

window.addEventListener("beforeunload", stop);
