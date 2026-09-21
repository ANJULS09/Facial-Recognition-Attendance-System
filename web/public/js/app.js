import { AttendanceLog, formatDate } from "./attendance.js";
import * as faces from "./faces.js";
import { DEFAULT_TOLERANCE, bestMatch, normalizeName } from "./matching.js";
import * as store from "./storage.js";

const MAX_SAMPLES_PER_PERSON = 10;

const $ = (id) => document.getElementById(id);
const el = {
  status: $("status"),
  toast: $("toast"),
  video: $("video"),
  overlay: $("overlay"),
  placeholder: $("placeholder"),
  toggleCamera: $("toggle-camera"),
  tolerance: $("tolerance"),
  toleranceValue: $("tolerance-value"),
  enrolForm: $("enrol-form"),
  name: $("name"),
  photos: $("photos"),
  addPhotos: $("add-photos"),
  snapshot: $("snapshot"),
  enrolMessage: $("enrol-message"),
  people: $("people"),
  showAll: $("show-all"),
  exportCsv: $("export-csv"),
  clearAttendance: $("clear-attendance"),
  attendanceBody: $("attendance-body"),
  attendanceEmpty: $("attendance-empty"),
  attendanceTable: $("attendance-table"),
  deleteAll: $("delete-all"),
};

let people = store.loadPeople(); // [{ name, samples: [{ descriptor, thumb }] }]
let samples = []; // flat [{ name, descriptor }] used for matching
const log = new AttendanceLog(store.loadAttendance());
let tolerance = DEFAULT_TOLERANCE;
let modelsReady = false;
let stream = null;
let running = false;
let enrolling = false;

// ---------------------------------------------------------------- helpers

function setStatus(text, kind = "") {
  el.status.textContent = text;
  el.status.className = `status ${kind}`.trim();
}

let toastTimer;
function toast(text) {
  el.toast.textContent = text;
  el.toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.toast.classList.remove("show"), 3000);
}

function setEnrolMessage(text, kind = "") {
  el.enrolMessage.textContent = text;
  el.enrolMessage.className = `message ${kind}`.trim();
}

function persistPeople() {
  samples = people.flatMap((p) => p.samples.map((s) => ({ name: p.name, descriptor: s.descriptor })));
  if (!store.savePeople(people)) {
    setEnrolMessage("Could not save to browser storage (full or disabled). Changes will be lost on reload.", "error");
  }
}

function persistAttendance() {
  if (!store.saveAttendance(log.records)) {
    toast("Could not save attendance to browser storage.");
  }
}

function syncButtons() {
  el.toggleCamera.disabled = !modelsReady;
  el.addPhotos.disabled = !modelsReady || enrolling;
  el.snapshot.disabled = !modelsReady || enrolling || !running;
}

// ---------------------------------------------------------------- rendering

function renderPeople() {
  el.people.replaceChildren();
  for (const person of people) {
    const item = document.createElement("li");

    const thumbs = document.createElement("div");
    thumbs.className = "thumbs";
    for (const sample of person.samples.filter((s) => s.thumb).slice(0, 3)) {
      const img = document.createElement("img");
      img.src = sample.thumb;
      img.alt = "";
      thumbs.append(img);
    }

    const label = document.createElement("div");
    label.className = "person-label";
    const name = document.createElement("strong");
    name.textContent = person.name;
    const count = document.createElement("span");
    count.textContent = `${person.samples.length} photo${person.samples.length === 1 ? "" : "s"}`;
    label.append(name, count);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "link danger";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove ${person.name}`);
    remove.addEventListener("click", () => {
      people = people.filter((p) => p !== person);
      persistPeople();
      renderPeople();
    });

    item.append(thumbs, label, remove);
    el.people.append(item);
  }
  if (people.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "No one enrolled yet.";
    el.people.append(empty);
  }
}

function renderAttendance() {
  const rows = (el.showAll.checked ? log.records : log.on()).slice().reverse();
  el.attendanceBody.replaceChildren();
  for (const record of rows) {
    const tr = document.createElement("tr");
    for (const value of [record.name, record.date, record.time]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    el.attendanceBody.append(tr);
  }
  el.attendanceTable.hidden = rows.length === 0;
  el.attendanceEmpty.hidden = rows.length > 0;
  el.exportCsv.disabled = log.records.length === 0;
  el.clearAttendance.disabled = log.records.length === 0;
}

// ---------------------------------------------------------------- enrolment

async function enrol(rawName, sources) {
  const name = normalizeName(rawName);
  if (!name) return setEnrolMessage("Enter a name first.", "error");
  if (sources.length === 0) return setEnrolMessage("Choose at least one photo, or use a camera snapshot.", "error");

  enrolling = true;
  syncButtons();
  setEnrolMessage("Analysing photos…");

  let person = people.find((p) => p.name === name);
  const isNew = !person;
  person ??= { name, samples: [] };

  let added = 0;
  let multiFace = 0;
  const skipped = [];
  for (const { label, load } of sources) {
    if (person.samples.length >= MAX_SAMPLES_PER_PERSON) {
      skipped.push(`${label} (limit of ${MAX_SAMPLES_PER_PERSON} photos per person)`);
      continue;
    }
    try {
      const image = await load();
      const result = await faces.describeStill(image);
      if (!result) {
        skipped.push(`${label} (no face found)`);
        continue;
      }
      if (result.count > 1) multiFace++;
      person.samples.push({
        descriptor: result.face.descriptor,
        thumb: faces.cropThumbnail(image, result.face.box),
      });
      added++;
    } catch {
      skipped.push(`${label} (couldn't read image)`);
    }
  }

  if (added > 0 && isNew) people.push(person);
  if (added > 0) {
    people.sort((a, b) => a.name.localeCompare(b.name));
    persistPeople();
    renderPeople();
  }

  const parts = [];
  if (added > 0) parts.push(`Added ${added} photo${added === 1 ? "" : "s"} for ${name}.`);
  if (multiFace > 0) parts.push(`${multiFace} had several faces; the largest was used.`);
  if (skipped.length > 0) parts.push(`Skipped: ${skipped.join(", ")}.`);
  setEnrolMessage(parts.join(" "), added > 0 ? "ok" : "error");

  enrolling = false;
  syncButtons();
  return added;
}

el.enrolForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const files = [...el.photos.files];
  const added = await enrol(
    el.name.value,
    files.map((file) => ({ label: file.name, load: () => faces.loadImage(file) })),
  );
  if (added) {
    el.photos.value = "";
    el.name.value = "";
  }
});

el.snapshot.addEventListener("click", async () => {
  const frame = document.createElement("canvas");
  frame.width = el.video.videoWidth;
  frame.height = el.video.videoHeight;
  frame.getContext("2d").drawImage(el.video, 0, 0);
  const added = await enrol(el.name.value, [{ label: "snapshot", load: async () => frame }]);
  if (added) el.name.value = "";
});

// ---------------------------------------------------------------- camera + recognition

const nextFrame = () => new Promise((resolve) => requestAnimationFrame(resolve));

function cameraErrorMessage(error) {
  switch (error?.name) {
    case "NotAllowedError":
      return "Camera permission was denied. Allow camera access in your browser and try again.";
    case "NotFoundError":
      return "No camera was found on this device.";
    case "NotReadableError":
      return "The camera is in use by another app.";
    default:
      return "Could not start the camera.";
  }
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    return setStatus("This browser can't access the camera (it needs HTTPS).", "error");
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
  } catch (error) {
    return setStatus(cameraErrorMessage(error), "error");
  }

  el.video.srcObject = stream;
  await el.video.play();
  el.overlay.width = el.video.videoWidth;
  el.overlay.height = el.video.videoHeight;
  el.placeholder.hidden = true;
  el.toggleCamera.textContent = "Stop camera";
  running = true;
  syncButtons();
  setStatus("Camera on", "ok");
  recognitionLoop();
}

function stopCamera() {
  running = false;
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
  el.video.srcObject = null;
  el.overlay.getContext("2d").clearRect(0, 0, el.overlay.width, el.overlay.height);
  el.placeholder.hidden = false;
  el.toggleCamera.textContent = "Start camera";
  syncButtons();
  setStatus("Ready", "ok");
}

async function recognitionLoop() {
  while (running) {
    if (el.video.readyState >= 2) {
      try {
        const detections = await faces.detectLive(el.video);
        if (!running) break;
        handleDetections(detections);
      } catch (error) {
        console.error(error);
      }
    }
    await nextFrame();
  }
}

function handleDetections(detections) {
  const ctx = el.overlay.getContext("2d");
  ctx.clearRect(0, 0, el.overlay.width, el.overlay.height);
  const fontSize = Math.max(14, Math.round(el.overlay.width / 45));
  ctx.font = `600 ${fontSize}px system-ui, sans-serif`;
  ctx.lineWidth = Math.max(2, Math.round(el.overlay.width / 400));

  for (const { box, descriptor } of detections) {
    const { name } = bestMatch(samples, descriptor, tolerance);
    const color = name ? "#16a34a" : "#dc2626";
    const label = name ?? "UNKNOWN";

    ctx.strokeStyle = color;
    ctx.strokeRect(box.x, box.y, box.width, box.height);

    const barHeight = fontSize + 10;
    const barWidth = Math.max(box.width, ctx.measureText(label).width + 12);
    ctx.fillStyle = color;
    ctx.fillRect(box.x, box.y + box.height, barWidth, barHeight);
    ctx.fillStyle = "#fff";
    ctx.textBaseline = "middle";
    ctx.fillText(label, box.x + 6, box.y + box.height + barHeight / 2);

    if (name && log.mark(name)) {
      persistAttendance();
      renderAttendance();
      toast(`Marked present: ${name}`);
    }
  }
}

el.toggleCamera.addEventListener("click", () => (running ? stopCamera() : startCamera()));

el.tolerance.addEventListener("input", () => {
  tolerance = Number(el.tolerance.value);
  el.toleranceValue.textContent = tolerance.toFixed(2);
});

window.addEventListener("pagehide", () => stream?.getTracks().forEach((track) => track.stop()));

// ---------------------------------------------------------------- attendance actions

el.showAll.addEventListener("change", renderAttendance);

el.exportCsv.addEventListener("click", () => {
  const blob = new Blob([log.toCSV()], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `attendance-${formatDate(new Date())}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
});

el.clearAttendance.addEventListener("click", () => {
  if (!confirm("Delete all attendance records from this browser?")) return;
  log.clear();
  persistAttendance();
  renderAttendance();
});

el.deleteAll.addEventListener("click", () => {
  if (!confirm("Delete all enrolled faces and attendance records from this browser?")) return;
  store.clearAll();
  people = [];
  log.clear();
  persistPeople();
  renderPeople();
  renderAttendance();
  setEnrolMessage("All local data deleted.", "ok");
});

// ---------------------------------------------------------------- start-up

samples = people.flatMap((p) => p.samples.map((s) => ({ name: p.name, descriptor: s.descriptor })));
renderPeople();
renderAttendance();
syncButtons();

setStatus("Loading face models…");
faces
  .loadModels()
  .then(() => {
    modelsReady = true;
    syncButtons();
    setStatus("Ready", "ok");
  })
  .catch((error) => {
    console.error(error);
    setStatus("Couldn't load the face models. Check your connection and reload.", "error");
  });
