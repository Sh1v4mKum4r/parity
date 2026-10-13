// Records Claude playing demo/parity-3d.html to an MP4.
//
//   node tools/record-playthrough.mjs [--seed N] [--out recordings/claude-plays-parity.mp4]
//
// It serves the repo itself, opens the game in headless Chrome with ?rec=1 (the
// built-in player on a fixed 1/30 s clock), steps it one frame at a time over the
// DevTools protocol, screenshots every frame, and encodes them with the ffmpeg
// that ships inside Python's imageio-ffmpeg. No npm packages: Node 22+ has
// fetch and WebSocket built in.
import { spawn, execFileSync } from "node:child_process";
import { createServer } from "node:http";
import { mkdirSync, writeFileSync, rmSync, readFileSync, existsSync } from "node:fs";
import { join, resolve, extname, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const arg = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i+1] : d; };
const SEED = arg("seed", String(Math.floor(Math.random() * 1e6)));
const OUT = resolve(ROOT, arg("out", "recordings/claude-plays-parity.mp4"));
const MAXF = +arg("max-frames", "9000");             // five minutes at 30 fps
const W = 1280, H = 720, PORT = 9333;
const CHROMES = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome", "/usr/bin/chromium",
];
const CHROME = CHROMES.find(existsSync);
if(!CHROME) throw new Error("no Chrome or Edge found");
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- serve the repo
const TYPES = { ".html":"text/html; charset=utf-8", ".js":"text/javascript", ".css":"text/css", ".png":"image/png", ".json":"application/json" };
const server = createServer((req, res) => {
  const p = join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if(!p.startsWith(ROOT) || !existsSync(p)){ res.writeHead(404); res.end(); return; }
  try { const body = readFileSync(p); res.writeHead(200, {"content-type": TYPES[extname(p)] || "application/octet-stream"}); res.end(body); }
  catch { res.writeHead(404); res.end(); }
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const url = `http://127.0.0.1:${server.address().port}/demo/parity-3d.html?rec=1&preserve&seed=${SEED}`;

// ---- headless Chrome
const work = join(tmpdir(), "parity-rec-" + process.pid);
const frames = join(work, "frames");
mkdirSync(frames, { recursive: true });
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${join(work, "profile")}`,
  `--window-size=${W},${H}`, "--hide-scrollbars", "--mute-audio", "--no-first-run", "--no-default-browser-check",
  "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "about:blank"], { stdio: "ignore" });

// Chrome's own start-up tab can be navigated out from under us a moment after it
// loads, so the game gets a tab of its own, opened straight at the game's URL.
let wsUrl = null;
for(let i = 0; i < 100 && !wsUrl; i++){
  // encoded, or Chrome cuts the URL at its first "&" and the seed is lost
  try { const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(url)}`, { method: "PUT" })).json();
        wsUrl = t.webSocketDebuggerUrl; } catch {}
  if(!wsUrl) await sleep(200);
}
if(!wsUrl) throw new Error("Chrome did not open a debugging port");
const ws = new WebSocket(wsUrl);
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let id = 0; const pending = new Map();
// Headless Chrome reloads a freshly opened tab once, a few seconds in, on its own.
// Every main-frame navigation is counted, so the capture can wait it out and, if
// one still lands mid-recording, start again rather than splice two runs together.
let navs = 0, lastNavAt = Date.now();
ws.onmessage = ev => { const m = JSON.parse(ev.data);
  if(m.method === "Page.frameNavigated" && !m.params.frame.parentId){ navs++; lastNavAt = Date.now(); }
  if(m.method === "Runtime.exceptionThrown")
    console.error("page error: " + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
  if(m.id && pending.has(m.id)){ const { res, rej } = pending.get(m.id); pending.delete(m.id);
    m.error ? rej(new Error(m.error.message)) : res(m.result); } };
const send = (method, params = {}) => new Promise((res, rej) => {
  const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async expr => {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
  if(r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || "page error");
  return r.result.value;
};

try {
  await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send("Page.enable");
  await send("Runtime.enable");
  // ready = the game is loaded, its clock is at zero, and nothing has navigated for 4 s
  async function settle(){
    for(let i = 0; i < 300; i++){
      let ok = false;
      try { ok = await evaluate("document.readyState === 'complete' && typeof window.__parityStep === 'function'"); } catch {}
      if(ok && Date.now() - lastNavAt > 4000) return;
      await sleep(200);
    }
    throw new Error("the game never settled at " + url);
  }

  let n = 0, st = null;
  for(let attempt = 1; ; attempt++){
    await settle();
    if((await evaluate("window.__parityStep(0)")).t !== 0){
      if(attempt > 3) throw new Error("the game clock would not start at zero");
      await send("Page.reload"); continue;
    }
    console.log(`recording seed ${SEED}` + (attempt > 1 ? ` (attempt ${attempt})` : ""));
    const navsAtStart = navs;
    n = 0;
    let broken = false;
    while(n < MAXF){
      try { st = await evaluate("window.__parityStep(1)"); } catch { broken = true; break; }
      if(navs !== navsAtStart){ broken = true; break; }
      const shot = await send("Page.captureScreenshot", { format: "jpeg", quality: 90 });
      writeFileSync(join(frames, String(n).padStart(5, "0") + ".jpg"), Buffer.from(shot.data, "base64"));
      n++;
      if(n % 300 === 0) console.log(`  ${n} frames  ·  ${st.t}s  ·  sent ${st.sent}/2  ·  taken ${st.caught}x`);
      if(st.done) break;
    }
    if(!broken) break;
    if(attempt >= 3) throw new Error("the page kept reloading during capture");
    console.log("  the page reloaded mid-capture; starting over");
    rmSync(frames, { recursive: true, force: true }); mkdirSync(frames, { recursive: true });
  }
  console.log(`captured ${n} frames: ${st.won ? "WON" : "did not finish"}, sent ${st.sent}/2, taken ${st.caught}x`);

  // ---- encode
  const ffmpeg = execFileSync("python", ["-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"]).toString().trim();
  mkdirSync(dirname(OUT), { recursive: true });
  execFileSync(ffmpeg, ["-y", "-loglevel", "error", "-framerate", "30", "-i", join(frames, "%05d.jpg"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", OUT]);
  console.log("wrote " + OUT);
} finally {
  ws.close(); chrome.kill(); server.close();
  await sleep(800);
  // Chrome can still be letting go of its profile; a stale temp folder is harmless
  try { rmSync(work, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }); }
  catch { console.log("note: could not remove " + work); }
}
