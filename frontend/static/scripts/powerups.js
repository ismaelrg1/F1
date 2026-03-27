(() => {
    const panel = document.querySelector(".powerups-panel");
    if (!panel) return;

    const race = panel.getAttribute("data-race");
    const year = parseInt(panel.getAttribute("data-year"), 10);
    const pendingKey = `powerup_pending_${race}_${year}`;
    const statusEl = panel.querySelector(".powerups-status");
    const controls = panel.querySelector(".powerups-controls");
    const typeSelect = panel.querySelector("#powerup-type");
    const targetWrapper = panel.querySelector("#powerup-target-wrapper");
    const targetSelect = panel.querySelector("#powerup-target");
    const applyBtn = panel.querySelector("#powerup-apply");
    const locked = panel.getAttribute("data-locked") === "true";

    const renderTargets = (targets) => {
        targetSelect.innerHTML = "";
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Selecciona usuario";
        targetSelect.appendChild(placeholder);
        targets.forEach((t) => {
            const opt = document.createElement("option");
            opt.value = t.id;
            opt.textContent = t.username;
            targetSelect.appendChild(opt);
        });
    };

    const setPendingUI = (pending) => {
        if (pending) {
            applyBtn.textContent = "✔ Seleccionado";
            applyBtn.classList.add("powerup-selected");
        } else {
            applyBtn.textContent = "Aplicar";
            applyBtn.classList.remove("powerup-selected");
        }
    };

    const loadStatus = async () => {
        const res = await fetch(`/api/powerups/status/${encodeURIComponent(race)}-${year}`, {
            credentials: "include",
        });
        const data = await res.json();
        if (!res.ok) {
            statusEl.textContent = data.error || "No se pudo cargar power-ups.";
            return;
        }

        const inv = data.inventory || {};
        const allowed = data.allowed_powerups || ["x2", "/2"];

        let badges = [];
        if (allowed.includes("x2")) {
            badges.push(`<span class="powerups-badge" data-tip="x2 → multiplica tus puntos x2.">x2: ${inv["x2"] || 0}</span>`);
        }
        if (allowed.includes("/2")) {
            badges.push(`<span class="powerups-badge" data-tip="/2 → divide los puntos de alguno de tus rivales (solo podrás ser penalizado en 2 GP diferentes).">/2: ${inv["/2"] || 0}</span>`);
        }

        statusEl.innerHTML = `<div class="powerups-badges">${badges.join("")}</div>`;

        if (locked) {
            controls.hidden = true;
            statusEl.innerHTML += `<div>⏳ Apuestas bloqueadas.</div>`;
            return;
        }

        if (data.used) {
            controls.hidden = true;
            statusEl.innerHTML += `<div>Ya usado: <strong>${data.used_powerup}</strong></div>`;
            localStorage.removeItem(pendingKey);
        } else {
            controls.hidden = false;
            renderTargets(data.targets || []);

            // --- Punto 3: limitar tipos permitidos según backend ---
            const allowed = data.allowed_powerups || ["x2", "/2"];

            Array.from(typeSelect.options).forEach((opt) => {
                if (!opt.value) return; // placeholder
                opt.disabled = !allowed.includes(opt.value);
            });

            if (typeSelect.value && !allowed.includes(typeSelect.value)) {
                typeSelect.value = "";
                targetWrapper.hidden = true;
                localStorage.removeItem(pendingKey);
                setPendingUI(false);
            }

            const pending = JSON.parse(localStorage.getItem(pendingKey) || "null");
            if (pending) {
                if (!allowed.includes(pending.powerup_type)) {
                    localStorage.removeItem(pendingKey);
                    setPendingUI(false);
                } else {
                    typeSelect.value = pending.powerup_type;
                    targetWrapper.hidden = pending.powerup_type !== "/2";
                    if (pending.target_user_id) {
                        targetSelect.value = String(pending.target_user_id);
                    }
                    setPendingUI(true);
                }
            } else {
                setPendingUI(false);
            }
        }
    };

    typeSelect.addEventListener("change", () => {
        targetWrapper.hidden = typeSelect.value !== "/2";
        localStorage.removeItem(pendingKey);
        setPendingUI(false);
    });

    applyBtn.addEventListener("click", async () => {
        if (locked) {
            alert("Las apuestas están bloqueadas.");
            return;
        }
        const existing = localStorage.getItem(pendingKey);
        if (existing) {
            localStorage.removeItem(pendingKey);
            setPendingUI(false);
            return;
        }

        const powerupType = typeSelect.value;
        if (!powerupType) {
            alert("Selecciona un power-up.");
            return;
        }
        let targetId = null;
        if (powerupType === "/2") {
            targetId = targetSelect.value;
            if (!targetId) {
                alert("Selecciona un objetivo.");
                return;
            }
        }
        localStorage.setItem(
            pendingKey,
            JSON.stringify({
                race,
                season_year: year,
                powerup_type: powerupType,
                target_user_id: targetId ? parseInt(targetId, 10) : null,
            })
        );
        setPendingUI(true);
    });

    window.__powerupPendingKey = pendingKey;
    loadStatus().catch(() => {
        statusEl.textContent = "No se pudo cargar power-ups.";
    });
})();
