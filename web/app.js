const el = (id) => document.getElementById(id);
const featureSel = el("feature");
const fileInput = el("file");
const paramsInput = el("params");
const statusBox = el("status");
const bar = el("bar");
const results = el("results");
const preview = el("preview");
const dropzone = document.getElementById("dropzone");
const toastEl = document.getElementById("toast");

// --- Helpers: overlay, compression, UA ---
const overlayEl = document.getElementById("overlay");
const overlayTextEl = document.getElementById("overlay-text");
function showOverlay(text){ if(overlayEl){ overlayEl.classList.remove("hidden"); if(overlayTextEl) overlayTextEl.textContent = text || "处理中..."; } }
function hideOverlay(){ if(overlayEl){ overlayEl.classList.add("hidden"); } }
function isMobile(){ return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent||""); }
function isWeChat(){ return /MicroMessenger/i.test(navigator.userAgent||""); }
async function compressImage(file, maxDim=1024, quality=0.85){
  return new Promise((resolve)=>{
    try{
      const img = new Image();
      img.onload = ()=>{
        const w = img.naturalWidth||img.width; const h = img.naturalHeight||img.height;
        const scale = Math.min(1, maxDim/Math.max(w,h));
        const nw = Math.round(w*scale), nh = Math.round(h*scale);
        const canvas = document.createElement("canvas");
        canvas.width = nw; canvas.height = nh;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, nw, nh);
        canvas.toBlob((blob)=>{
          if(!blob){ resolve(file); return; }
          const name = (file.name||"upload").replace(/\.[^.]+$/, "") + ".jpg";
          const out = new File([blob], name, {type:"image/jpeg", lastModified: Date.now()});
          resolve(out);
        }, "image/jpeg", quality);
      };
      img.onerror = ()=> resolve(file);
      img.src = URL.createObjectURL(file);
    }catch(e){ resolve(file); }
  });
}
function showMobileSaveTipOnce(){
  if(!isMobile()) return;
  if(sessionStorage.getItem("mobileTipShown")==="1") return;
  const text = isWeChat()? "长按图片即可保存到相册（微信内置浏览器）" : "Tap and hold to save image";
  const tip = document.createElement("div");
  tip.className = "mobile-tip";
  tip.innerHTML = `<span>${text}</span><span class="close">✕</span>`;
  tip.querySelector(".close")?.addEventListener("click", ()=>{ try{ document.body.removeChild(tip);}catch(_){}});
  document.body.appendChild(tip);
  sessionStorage.setItem("mobileTipShown","1");
  setTimeout(()=>{ try{ document.body.contains(tip) && document.body.removeChild(tip);}catch(_){}} , 6000);
}

// --- Era style guidance ---
function applyEraStyleGuide(){
  if (!paramsInput) return;
  const sample = { era: "1970", gender: "男性", hair: "长卷发", face: "长胡子", backdrop: "北京胡同夏日风景" };
  paramsInput.placeholder = JSON.stringify(sample, null, 2);
  let guide = document.getElementById("era-guide");
  if (!guide) {
    guide = document.createElement("div");
    guide.id = "era-guide";
    guide.style.cssText = "margin-top:8px;font-size:12px;color:#334155;background:#f8fafc;border:1px solid #e2e8f0;padding:10px;border-radius:8px;";
    paramsInput.parentElement?.appendChild(guide);
  }
  guide.innerHTML = `
    <div style="font-weight:600;margin-bottom:6px;">时代风格转换提示：</div>
    <div>将角色的风格改为[1970]年代的经典[男性]风格</div>
    <div>添加[长卷发]，[长胡子]，将背景改为标志性的[北京胡同夏日风景]</div>
    <div>不要改变角色的面部</div>
    <div style="margin-top:6px;color:#64748b;">请把方括号 [] 中的内容替换为你想要的描述；或在上方“高级参数（JSON）”中填写：<code>{"era":"1970","gender":"男性","hair":"长卷发","face":"长胡子","backdrop":"北京胡同夏日风景"}</code></div>
  `;
}
function clearEraStyleGuide(){
  if (!paramsInput) return;
  const guide = document.getElementById("era-guide");
  if (guide && guide.parentElement) guide.parentElement.removeChild(guide);
}

// --- Reference data for features ---
const REF_DATA = {
  enhance: {
    img: "./assets/enhance.svg",
    title: "智能修图增强",
    desc: "自动提亮、降噪与轻度美化，保持自然不过度。",
  },
  figurine: {
    img: "./assets/figurine2.svg",
    title: "插画转手办",
    desc: "将插画主体转为 3D 手办风格，突出造型与质感。",
  },
  era_style: {
    img: "./assets/era_style2.svg",
    title: "时代风格转换",
    desc: "一键迁移到特定年代风格，保留人物主体特征。",
  },
  hairstyle_grid: {
    img: "./assets/hairstyle.svg",
    title: "发型九宫格",
    desc: "尝试多种发型并一次性对比，选出更适合的造型。",
  },
  old_photo_restore: {
    img: "./assets/old_photo.svg",
    title: "老照片修复上色",
    desc: "修复划痕、降噪并自然上色，保留时代质感。",
  },
  id_photo: {
    img: "./assets/id_photo.svg",
    title: "证件照制作",
    desc: "规范背景与构图，输出标准证件照尺寸。",
  },
};

function updateRef(val){
  const d = REF_DATA[val] || REF_DATA.enhance;
  const img = document.getElementById("ref-img");
  const t = document.getElementById("ref-title");
  const s = document.getElementById("ref-desc");
  if (img) img.src = d.img;
  if (t) t.textContent = d.title;
  if (s) s.textContent = d.desc;
}

// --- Feature chips ---
const chipsWrap = document.getElementById("feature-chips");
if (chipsWrap) {
  chipsWrap.addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    const val = btn.getAttribute("data-value");
    document.querySelectorAll("#feature-chips .chip").forEach((c) => c.classList.remove("chip-active"));
    btn.classList.add("chip-active");
    if (featureSel) featureSel.value = val;
    updateRef(val);
    if (val === "era_style") applyEraStyleGuide(); else clearEraStyleGuide();
  });
}

// --- File select / preview ---
fileInput.addEventListener("change", () => updatePreview());
function updatePreview(){
  const f = fileInput.files?.[0];
  if (!f) return (preview.innerHTML = "");
  const url = URL.createObjectURL(f);
  preview.innerHTML = `<img src="${url}" alt="preview"/>`;
}

// --- Drag & Drop ---
if (dropzone) {
  ["dragenter","dragover"].forEach(ev => dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  }));
  ;["dragleave","drop"].forEach(ev => dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  }));
  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    if (!dt || !dt.files || !dt.files[0]) return;
    const f = dt.files[0];
    try {
      const d = new DataTransfer();
      d.items.add(f);
      fileInput.files = d.files;
    } catch (_) {}
    updatePreview();
  });
}

// --- Submit ---
el("submit").addEventListener("click", async () => {
  const f = fileInput.files?.[0];
  if (!f) return toast("请先选择图片");

  let params = {};
  try { params = paramsInput.value ? JSON.parse(paramsInput.value) : {}; } catch (e) { return toast("参数必须是 JSON"); }

  showOverlay("正在准备与上传图片...");
  let cf = f;
  try {
    cf = await compressImage(f, 1024, 0.85);
    if (cf.size < f.size) {
      toast(`已压缩：${(f.size/1024/1024).toFixed(2)}MB → ${(cf.size/1024/1024).toFixed(2)}MB`);
    }
  } catch (_) {}

  const form = new FormData();
  form.append("type", featureSel.value);
  form.append("params", JSON.stringify(params));
  form.append("file", cf, cf.name || "upload.jpg");

  setProgress(3, "创建任务中...");
  const btn = el("submit");
  btn.disabled = true; btn.classList.add("opacity-70"); btn.textContent = "处理中...";
  try {
    const r = await fetch("/api/jobs", { method: "POST", body: form });
    if (!r.ok) throw new Error("创建任务失败");
    const { job_id } = await r.json();
    poll(job_id);
  } catch (err) {
    setProgress(0, "");
    toast(err.message || "网络错误");
    hideOverlay();
  } finally {
    btn.disabled = false; btn.classList.remove("opacity-70"); btn.textContent = "开始处理";
  }
});

async function poll(jobId){
  const poller = setInterval(async () => {
    try {
      const r = await fetch(`/api/jobs/${jobId}`);
      if (!r.ok) throw new Error("查询失败");
      const s = await r.json();
      setProgress(s.progress ?? 0, s.status);
      if (s.status === "finished") {
        clearInterval(poller);
        renderResults(s.results || []);
        toast("已完成");
        hideOverlay();
      }
      if (s.status === "failed") {
        clearInterval(poller);
        statusBox.textContent = `失败：${s.error || "未知错误"}`;
        toast("处理失败");
        hideOverlay();
      }
    } catch (e) {
      clearInterval(poller);
      setProgress(0, "");
      toast("查询失败");
      hideOverlay();
    }
  }, 1000);
}

function setProgress(p, text){
  bar.style.width = `${Math.min(100, Math.max(0, p))}%`;
  statusBox.textContent = text;
  if (overlayEl && !overlayEl.classList.contains('hidden') && overlayTextEl) {
    overlayTextEl.textContent = text || '处理中...';
  }
}

function renderResults(urls){
  results.innerHTML = urls.map(u => `
    <figure class="space-y-2">
      <img src="${u}" class="w-full rounded border border-slate-200"/>
      <div class="text-right">
        <a href="${u}" download class="text-sm text-blue-600 hover:underline">下载</a>
      </div>
    </figure>
  `).join("");
  showMobileSaveTipOnce();
}

function toast(text){
  if (!toastEl) return alert(text);
  toastEl.textContent = text;
  toastEl.classList.remove("hidden");
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.add("hide"), 10);
  setTimeout(() => { toastEl.classList.add("hidden"); toastEl.classList.remove("show","hide"); }, 2000);
}

// init ref on load
updateRef(featureSel?.value || "enhance");
if ((featureSel?.value||"") === "era_style") applyEraStyleGuide();
