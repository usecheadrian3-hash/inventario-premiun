/* ===== script.js � PREMIUM EDITION ===== */

(function() {

/* ?????????????????????????????????????????

   0. SOUND SYSTEM (OPCIONAL)

????????????????????????????????????????? */

const SoundFX = {

    _enabled: localStorage.getItem('sfx_enabled') !== 'false',

    _ctx: null,

    _init() {

        if (!this._ctx) this._ctx = new (window.AudioContext || window.webkitAudioContext)();

    },

    toggle() { this._enabled = !this._enabled; localStorage.setItem('sfx_enabled', this._enabled); return this._enabled; },

    play(type) {

        if (!this._enabled) return;

        try {

            this._init();

            const osc = this._ctx.createOscillator();

            const gain = this._ctx.createGain();

            osc.connect(gain); gain.connect(this._ctx.destination);

            gain.gain.value = 0.08;

            const freqs = { click: 800, success: 660, error: 220, notification: 520 };

            osc.frequency.value = freqs[type] || 400;

            osc.type = 'sine';

            osc.start();

            gain.gain.exponentialRampToValueAtTime(0.001, this._ctx.currentTime + 0.12);

            osc.stop(this._ctx.currentTime + 0.12);

        } catch(e) {}

    }

};

window.SoundFX = SoundFX;

/* ?????????????????????????????????????????

   1. PAGE TRANSITIONS

????????????????????????????????????????? */

document.addEventListener('click', function(e) {

    const link = e.target.closest('a[href]');

    if (!link) return;

    if (link.hasAttribute('onclick') || link.target === '_blank' || link.getAttribute('href').startsWith('#') ||

        link.getAttribute('href').startsWith('mailto:') || link.getAttribute('href').startsWith('javascript:') ||

        e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;

    const dest = link.href;

    if (!dest || dest === window.location.href) return;

    e.preventDefault();

    document.body.classList.add('page-exit');

    setTimeout(() => { window.location.href = dest; }, 260);

});

/* ?????????????????????????????????????????

   2. SMOOTH SCROLL & NAVBAR

????????????????????????????????????????? */

const navbar = document.getElementById('navbar');

if (navbar) {

    window.addEventListener('scroll', () => { navbar.classList.toggle('scrolled', window.scrollY > 40); });

}

function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }); }

document.querySelectorAll('a[href^="#"]').forEach(a => {

    a.addEventListener('click', function(e) {

        const target = document.querySelector(this.getAttribute('href'));

        if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }

    });

});

/* ?????????????????????????????????????????

   3. GLOBAL TOAST

????????????????????????????????????????? */

const ICONS = { success: '?', error: '?', warning: '??', info: '??' };

function mostrarAlerta(mensaje, tipo = 'success') {

    SoundFX.play(tipo === 'error' ? 'error' : tipo === 'success' ? 'success' : 'click');

    const existing = document.querySelectorAll('.alerta');

    if (existing.length >= 3) existing[0].remove();

    const alerta = document.createElement('div');

    alerta.className = `alerta ${tipo}`;

    const offset = existing.length * 80;

    alerta.style.bottom = `${1.5 * 16 + offset}px`;

    alerta.innerHTML = `<span>${ICONS[tipo] || '?'}</span><span>${mensaje}</span>`;

    document.body.appendChild(alerta);

    requestAnimationFrame(() => { requestAnimationFrame(() => alerta.classList.add('mostrar')); });

    setTimeout(() => {

        alerta.classList.remove('mostrar');

        alerta.style.opacity = '0';

        setTimeout(() => alerta.remove(), 400);

    }, 3200);

}

window.mostrarAlerta = mostrarAlerta;

/* ?????????????????????????????????????????

   4. FORM VALIDATION

????????????????????????????????????????? */

document.querySelectorAll('form').forEach(form => {

    form.addEventListener('submit', (e) => {

        const inputs = form.querySelectorAll('input[required]');

        let valido = true;

        inputs.forEach(input => {

            if (input.value.trim() === '') {

                valido = false;

                input.style.borderColor = '#ef4444';

                input.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.18)';

                setTimeout(() => {

                    input.style.borderColor = '';

                    input.style.boxShadow = '';

                }, 400);

            }

        });

        if (!valido) { e.preventDefault(); mostrarAlerta('Completa todos los campos requeridos', 'error'); }

    });

});

/* ?????????????????????????????????????????

   5. BUSCADOR

????????????????????????????????????????? */

document.querySelectorAll('#buscador').forEach(b => {

    b.addEventListener('keyup', () => {

        const texto = b.value.toLowerCase();

        document.querySelectorAll('.producto').forEach(p => {

            p.style.display = p.innerText.toLowerCase().includes(texto) ? '' : 'none';

        });

    });

});

/* ?????????????????????????????????????????

   6. CONFIRMAR ELIMINAR

????????????????????????????????????????? */

document.querySelectorAll('.btn-eliminar').forEach(btn => {

    btn.addEventListener('click', (e) => {

        SoundFX.play('click');

        if (!confirm('�Seguro que deseas eliminar este producto?')) e.preventDefault();

    });

});

/* ?????????????????????????????????????????

   7. SCROLL REVEAL

????????????????????????????????????????? */

(function() {

    const revealEls = document.querySelectorAll('.reveal');

    if (!revealEls.length) return;

    const observer = new IntersectionObserver((entries) => {

        entries.forEach(entry => {

            if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }

        });

    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

    revealEls.forEach(el => observer.observe(el));

})();

/* ?????????????????????????????????????????

   8. RIPPLE EFFECT

????????????????????????????????????????? */

(function() {

    function createRipple(e) {

        const btn = e.currentTarget;

        if (!btn.style.position || btn.style.position === 'static') btn.style.position = 'relative';

        btn.style.overflow = 'hidden';

        const circle = document.createElement('span');

        const diameter = Math.max(btn.clientWidth, btn.clientHeight);

        const rect = btn.getBoundingClientRect();

        circle.classList.add('ripple-wave');

        circle.style.width = circle.style.height = diameter + 'px';

        circle.style.left = (e.clientX - rect.left - diameter / 2) + 'px';

        circle.style.top = (e.clientY - rect.top - diameter / 2) + 'px';

        const existing = btn.querySelector('.ripple-wave');

        if (existing) existing.remove();

        btn.appendChild(circle);

        circle.addEventListener('animationend', () => circle.remove());

    }

    function applyRipple() {

        document.querySelectorAll('button:not([class*="hamburger"]), .btn-ingresar, .btn-nav-register').forEach(btn => {

            if (btn.dataset.ripple) return;

            btn.dataset.ripple = '1';

            btn.addEventListener('click', createRipple);

        });

    }

    applyRipple();

    const mo = new MutationObserver(applyRipple);

    mo.observe(document.body, { childList: true, subtree: true });

})();

/* ?????????????????????????????????????????

   9. SHAKE ANIMATION CSS INJECTION

????????????????????????????????????????? */

if (!document.getElementById('shake-style')) {

    const s = document.createElement('style');

    s.id = 'shake-style';

    s.textContent = `@keyframes shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-7px)}40%{transform:translateX(7px)}60%{transform:translateX(-4px)}80%{transform:translateX(4px)}}@keyframes ripple-wave{0%{transform:scale(0);opacity:.5}100%{transform:scale(4);opacity:0}}.ripple-wave{position:absolute;border-radius:50%;background:rgba(255,255,255,0.3);pointer-events:none;animation:ripple-wave .6s ease-out}`;

    document.head.appendChild(s);

}

/* ?????????????????????????????????????????

   10. IVA CALCULATOR

????????????????????????????????????????? */

function calcularPrecioConIVA(precio, iva) {

    return precio + (precio * iva / 100);

}

function actualizarIVA() {

    const precioInput = document.querySelector('input[name="precio"]');

    const ivaInput = document.querySelector('input[name="iva"]');

    const precioConIVASpan = document.getElementById('precio-con-iva-display');

    if (precioInput && ivaInput && precioConIVASpan) {

        const p = parseFloat(precioInput.value) || 0;

        const i = parseFloat(ivaInput.value) || 0;

        precioConIVASpan.textContent = '$' + calcularPrecioConIVA(p, i).toFixed(2);

    }

}

document.querySelectorAll('input[name="precio"], input[name="iva"]').forEach(el => {

    el.addEventListener('input', actualizarIVA);

});

document.addEventListener('DOMContentLoaded', actualizarIVA);

/* ?????????????????????????????????????????

   11. DASHBOARD CHARTS (global function)

????????????????????????????????????????? */

window.initDashboardCharts = function() {

    fetch('/api/dashboard_data').then(r => r.json()).then(data => {

        if (!data || !data.top_productos) return;

        // Top Products Chart (bar)

        const ctx1 = document.getElementById('chart-top-productos');

        if (ctx1 && data.top_productos.length) {

            new Chart(ctx1, {

                type: 'bar',

                data: {

                    labels: data.top_productos.map(p => p[0]),

                    datasets: [{

                        label: 'Cantidad',

                        data: data.top_productos.map(p => p[1]),

                        backgroundColor: 'rgba(124,58,237,0.6)',

                        borderColor: '#7c3aed',

                        borderWidth: 1,

                        borderRadius: 4

                    }]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: { legend: { display: false } },

                    scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } }

                }

            });

        }

        // Best sellers (pie)

        const ctx2 = document.getElementById('chart-mas-vendidos');

        if (ctx2 && data.mas_vendidos.length) {

            new Chart(ctx2, {

                type: 'doughnut',

                data: {

                    labels: data.mas_vendidos.map(p => p[0]),

                    datasets: [{

                        data: data.mas_vendidos.map(p => p[1]),

                        backgroundColor: ['#7c3aed','#4c1d95','#a78bfa','#06b6d4','#8b5cf6'],

                        borderWidth: 0

                    }]

                },

                options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: 'rgba(255,255,255,0.7)', font: { size: 10 } } } } }

            });

        }

        // Least sellers

        const ctx3 = document.getElementById('chart-menos-vendidos');

        if (ctx3 && data.menos_vendidos.length) {

            new Chart(ctx3, {

                type: 'bar',

                data: {

                    labels: data.menos_vendidos.map(p => p[0]),

                    datasets: [{

                        label: 'Vendidos',

                        data: data.menos_vendidos.map(p => p[1]),

                        backgroundColor: 'rgba(239,68,68,0.6)',

                        borderColor: '#ef4444',

                        borderWidth: 1,

                        borderRadius: 4

                    }]

                },

                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } } }

            });

        }

        // Sales chart (line)

        const ctx4 = document.getElementById('chart-ventas');

        if (ctx4 && data.ventas_diarias && data.ventas_diarias.length) {

            new Chart(ctx4, {

                type: 'line',

                data: {

                    labels: data.ventas_diarias.map(v => v[0]),

                    datasets: [{

                        label: 'Ventas ($)',

                        data: data.ventas_diarias.map(v => v[1]),

                        borderColor: '#22c55e',

                        backgroundColor: 'rgba(34,197,94,0.1)',

                        fill: true,

                        tension: 0.4,

                        pointRadius: 3

                    }]

                },

                options: { responsive: true, plugins: { legend: { labels: { color: 'rgba(255,255,255,0.7)', font: { size: 11 } } } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } } }

            });

        }

    }).catch(() => {});

};

/* ?????????????????????????????????????????

   12. KPI CALCULATOR

????????????????????????????????????????? */

window.calcularKPIs = function() {

    const rows = document.querySelectorAll('#tablaInventario tbody tr.producto');

    let lowStock = 0, activos = 0, totalValue = 0, totalIVA = 0;

    rows.forEach(r => {

        const qty = parseInt(r.dataset.cantidad) || 0;

        const min = parseInt(r.dataset.stock) || 0;

        const price = parseFloat(r.dataset.precio) || 0;

        const iva = parseFloat(r.dataset.iva) || 19;

        const est = r.dataset.estado || '';

        if (qty <= min) lowStock++;

        if (est === 'Activo') activos++;

        totalValue += qty * price;

        totalIVA += qty * price * iva / 100;

    });

    const total = document.getElementById('kpi-total');

    const low = document.getElementById('kpi-lowstock');

    const act = document.getElementById('kpi-activos');

    const val = document.getElementById('kpi-value');

    if (total) total.textContent = rows.length;

    if (low) low.textContent = lowStock;

    if (act) act.textContent = activos;

    if (val) val.textContent = '$' + Math.round(totalValue + totalIVA).toLocaleString('es-CO');

    const valSin = document.getElementById('kpi-value-siniva');

    if (valSin) valSin.textContent = '$' + Math.round(totalValue).toLocaleString('es-CO');

};

/* ?????????????????????????????????????????

   13. PERFIL POPUP

????????????????????????????????????????? */

const perfilBtn = document.getElementById('perfilBtn');

const perfilPopup = document.getElementById('perfilPopup');

if (perfilBtn && perfilPopup) {

    document.addEventListener('click', e => { if (!perfilBtn.contains(e.target)) perfilPopup.classList.remove('abierto'); });

}

/* ?????????????????????????????????????????

   14. MODAL COMENTARIO

????????????????????????????????????????? */

function abrirComentario() { document.getElementById('modalComentario')?.classList.add('abierto'); }

function cerrarComentario() { document.getElementById('modalComentario')?.classList.remove('abierto'); }

function enviarComentario() {

    const texto = document.getElementById('textoComentario')?.value.trim();

    if (!texto) { mostrarAlerta('Escribe un comentario primero', 'error'); return; }

    cerrarComentario();

    document.getElementById('textoComentario').value = '';

    mostrarAlerta('�Comentario enviado! Gracias', 'success');

}

document.getElementById('modalComentario')?.addEventListener('click', function(e) { if (e.target === this) cerrarComentario(); });

/* ?????????????????????????????????????????

   15. EDIT MODAL

????????????????????????????????????????? */

window.abrirEditar = function(btn) {

    SoundFX.play('click');

    const d = btn.closest('tr').dataset;

    const fields = ['nombre','descripcion','cantidad','stock','precio','categoria','proveedor','fecha','estado','iva','etiquetas'];

    fields.forEach(f => {

        const el = document.getElementById('edit-' + f);

        if (el) el.value = d[f] || '';

    });

    document.getElementById('formEditar').action = '/editar/' + d.id;

    document.getElementById('modalEditOverlay').classList.add('abierto');

};

window.cerrarEditar = function() { document.getElementById('modalEditOverlay').classList.remove('abierto'); };

const editOverlay = document.getElementById('modalEditOverlay');

if (editOverlay) editOverlay.addEventListener('click', function(e) { if (e.target === this) cerrarEditar(); });

/* ?????????????????????????????????????????

   16. RECIBO / EXPORT (movido a blog.html)

????????????????????????????????????????? */

/*   17. MODE TOGGLE / CUSTOMIZATION

????????????????????????????????????????? */

function getStorageKey() {

    const avatar = document.getElementById('avatarTopbar');

    if (!avatar) return 'inv_prefs';

    return 'inv_' + (document.querySelector('[data-user-id]')?.dataset?.userId || '0');

}

function cargarPrefs() { try { return JSON.parse(localStorage.getItem(getStorageKey())) || {}; } catch (e) { return {}; } }

function guardarPrefs(p) { try { localStorage.setItem(getStorageKey(), JSON.stringify(p)); } catch (e) {} }

window.setModo = function(modo) {

    const p = cargarPrefs();

    p.modo = modo;

    guardarPrefs(p);

    aplicarModo(modo);

};

function aplicarModo(modo) {

    if (modo === 'claro') {

        document.body.classList.add('modo-claro');

        const btnClaro = document.getElementById('btnClaro');

        const btnOscuro = document.getElementById('btnOscuro');

        if (btnClaro) btnClaro.classList.add('activo');

        if (btnOscuro) btnOscuro.classList.remove('activo');

    } else {

        document.body.classList.remove('modo-claro');

        const btnOscuro = document.getElementById('btnOscuro');

        const btnClaro = document.getElementById('btnClaro');

        if (btnOscuro) btnOscuro.classList.add('activo');

        if (btnClaro) btnClaro.classList.remove('activo');

    }

}

function hexToRgb(hex) { const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16); return [r, g, b]; }

function rgbToHex(r, g, b) { return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join(''); }

function darkenColor(hex, amount) { amount = amount || 0.7; const [r, g, b] = hexToRgb(hex); return rgbToHex(Math.floor(r * amount), Math.floor(g * amount), Math.floor(b * amount)); }

function lightenColor(hex, amount) { amount = amount || 1.15; const [r, g, b] = hexToRgb(hex); return rgbToHex(Math.min(255, Math.floor(r * amount)), Math.min(255, Math.floor(g * amount)), Math.min(255, Math.floor(b * amount))); }

function hexToRgbaStr(hex, a) { const [r, g, b] = hexToRgb(hex); return `rgba(${r},${g},${b},${a})`; }

window.aplicarColor = function(c1, c2) {

    document.documentElement.style.setProperty('--blue', c1);

    document.documentElement.style.setProperty('--blue-dark', c2 || darkenColor(c1));

    document.documentElement.style.setProperty('--blue-light', lightenColor(c1));

    document.documentElement.style.setProperty('--blue-glow', hexToRgbaStr(c1, 0.35));

    document.documentElement.style.setProperty('--blue-soft', hexToRgbaStr(c1, 0.10));

    document.querySelectorAll('.color-dot').forEach(d => d.classList.toggle('activo', d.dataset.color === c1));

    const p = cargarPrefs();

    p.color1 = c1;

    p.color2 = c2 || darkenColor(c1);

    guardarPrefs(p);

};

window.aplicarColorPersonalizado = function() {

    aplicarColor(selectedHex || '#7c3aed', darkenColor(selectedHex || '#7c3aed'));

    cerrarRuedaColor();

    mostrarAlerta('Color aplicado', 'success');

};

function abrirRuedaColor() {

    const popup = document.getElementById('perfilPopup');

    if (popup) popup.classList.remove('abierto');

    document.getElementById('modalColorOverlay')?.classList.add('abierto');

    dibujarRueda();

}

window.abrirRuedaColor = abrirRuedaColor;

window.cerrarRuedaColor = function() { document.getElementById('modalColorOverlay')?.classList.remove('abierto'); };
document.getElementById('modalColorOverlay')?.addEventListener('click', function(e) { if (e.target === this) cerrarRuedaColor(); });

let selectedHex = '#7c3aed';

function dibujarRueda() {

    const wc = document.getElementById('colorWheel');

    if (!wc) return;

    const wctx = wc.getContext('2d');

    const cx = wc.width / 2, cy = wc.height / 2, r = cx - 4;

    for (let angle = 0; angle < 360; angle++) {

        const grad = wctx.createRadialGradient(cx, cy, 0, cx, cy, r);

        grad.addColorStop(0, 'white');

        grad.addColorStop(1, `hsl(${angle},100%,50%)`);

        wctx.beginPath();

        wctx.moveTo(cx, cy);

        wctx.arc(cx, cy, r, (angle - 1) * Math.PI / 180, (angle + 1) * Math.PI / 180);

        wctx.closePath();

        wctx.fillStyle = grad;

        wctx.fill();

    }

}

document.getElementById('colorWheel')?.addEventListener('click', function(e) {

    const rect = this.getBoundingClientRect();

    const px = this.getContext('2d').getImageData(e.clientX - rect.left, e.clientY - rect.top, 1, 1).data;

    selectedHex = rgbToHex(px[0], px[1], px[2]);

    const preview = document.getElementById('colorPreviewCircle');

    const input = document.getElementById('colorHexInput');

    if (preview) preview.style.background = selectedHex;

    if (input) input.value = selectedHex;

});

document.getElementById('colorHexInput')?.addEventListener('input', function() {

    if (/^#[0-9a-fA-F]{6}$/.test(this.value)) {

        selectedHex = this.value;

        const preview = document.getElementById('colorPreviewCircle');

        if (preview) preview.style.background = selectedHex;

    }

});

function aplicarPrefs() {

    const p = cargarPrefs();

    if (p.color1) aplicarColor(p.color1, p.color2);

    aplicarModo(p.modo || 'oscuro');

}

/* ?????????????????????????????????????????

   18. BIENVENIDA (solo portada)

????????????????????????????????????????? */

window.addEventListener('load', () => {

    const isPortada = document.querySelector('.contenido') && document.querySelector('.btn-ingresar');

    if (isPortada) {

        setTimeout(() => mostrarAlerta('Bienvenido al sistema', 'success'), 700);

    }

    aplicarPrefs();

});

/* ?????????????????????????????????????????

   19. SOUND TOGGLE (tecla S)

????????????????????????????????????????? */

document.addEventListener('keydown', (e) => {

    if (e.key === 's' && e.ctrlKey) {

        e.preventDefault();

        const enabled = SoundFX.toggle();

        mostrarAlerta(`Sonido: ${enabled ? 'Activado' : 'Desactivado'}`, 'info');

    }

});

/* ?????????????????????????????????????????

   20. PREMIUM NOTIFICATION SYSTEM

????????????????????????????????????????? */

(function() {

    if (window.PremiumToast) return;

    var container = document.querySelector('.premium-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'premium-toast-container';
        document.body.appendChild(container);
    }

    var counter = 0;

    window.PremiumToast = function(title, message, type) {
        type = type || 'info';
        var id = 'pt-' + (++counter);
        var icons = { success: '✅', error: '❌', warning: '⚠️', info: '💡' };
        var div = document.createElement('div');
        div.className = 'premium-toast ' + type;
        div.id = id;
        div.innerHTML =
            '<div class="premium-toast-icon">' + (icons[type] || '💡') + '</div>' +
            '<div class="premium-toast-body">' +
                '<div class="premium-toast-title">' + title + '</div>' +
                '<div class="premium-toast-msg">' + message + '</div>' +
            '</div>' +
            '<button class="premium-toast-close" onclick="window.PremiumToastRemove(\'' + id + '\')">✕</button>';
        container.appendChild(div);
        setTimeout(function() { window.PremiumToastRemove(id); }, 5000);
        return id;
    };

    window.PremiumToastRemove = function(id) {
        var el = document.getElementById(id);
        if (!el) return;
        if (el.classList.contains('removing')) return;
        el.classList.add('removing');
        setTimeout(function() { if (el.parentNode) el.parentNode.removeChild(el); }, 400);
    };

    // Replace old mostrarAlerta with premium version
    if (window.mostrarAlerta) {
        var oldAlert = window.mostrarAlerta;
        window.mostrarAlerta = function(msg, type) {
            type = type || 'success';
            var titles = { success: 'Operación exitosa', error: 'Error', warning: 'Advertencia', info: 'Información' };
            PremiumToast(titles[type] || 'Información', msg, type);
        };
    }
})();

/* ?????????????????????????????????????????

   21. GLOBAL SEARCH (Ctrl+K)

????????????????????????????????????????? */

(function() {

    if (window.__searchInited) return;
    window.__searchInited = true;

    var overlay = document.createElement('div');
    overlay.className = 'search-overlay';
    overlay.id = 'globalSearchOverlay';
    overlay.innerHTML =
        '<div class="search-modal">' +
            '<div class="search-modal-header">' +
                '<span class="search-icon">🔍</span>' +
                '<input type="text" id="searchInput" placeholder="Buscar productos, ventas, clientes, proveedores..." autocomplete="off" />' +
                '<span class="search-shortcut">ESC</span>' +
            '</div>' +
            '<div class="search-modal-body" id="searchResults"></div>' +
        '</div>';
    document.body.appendChild(overlay);

    var input = document.getElementById('searchInput');
    var results = document.getElementById('searchResults');

    var searchRoutes = [
        { label: 'Dashboard', url: '/blog', icon: '📊', keywords: 'inicio panel principal dashboard' },
        { label: 'Dashboard Premium', url: '/dashboard-premium', icon: '✦', keywords: 'premium ejecutivo panel' },
        { label: 'Ventas', url: '/ventas', icon: '🧾', keywords: 'ventas factura ticket cobro' },
        { label: 'Compras', url: '/compras', icon: '📦', keywords: 'compras proveedor进货' },
        { label: 'Clientes', url: '/clientes', icon: '👥', keywords: 'clientes客户' },
        { label: 'Proveedores', url: '/proveedores', icon: '📦', keywords: 'proveedores supplier' },
        { label: 'Categorías', url: '/categorias', icon: '📂', keywords: 'categorias类别' },
        { label: 'Gastos', url: '/gastos', icon: '💰', keywords: 'gastos expensas' },
        { label: 'Reportes', url: '/reportes', icon: '📈', keywords: 'reportes informes estadisticas' },
        { label: 'Perfil', url: '/perfil', icon: '👤', keywords: 'perfil usuario configuracion' },
        { label: 'Comentarios', url: '/comentarios', icon: '💬', keywords: 'comentarios feedback opinion' },
    ];

    var userRole = document.querySelector('[data-user-id]') ? (document.querySelector('.role-badge') ? document.querySelector('.role-badge').textContent.trim() : '') : '';
    if (userRole === 'admin') {
        searchRoutes.push({ label: 'Admin Panel', url: '/admin', icon: '🔰', keywords: 'admin administrador panel' });
        searchRoutes.push({ label: 'Admin - Usuarios', url: '/admin/usuarios', icon: '👥', keywords: 'admin usuarios gestion' });
        searchRoutes.push({ label: 'Admin - Historial', url: '/admin/historial', icon: '📋', keywords: 'admin historial log' });
        searchRoutes.push({ label: 'Admin - Actividad', url: '/admin/actividad', icon: '⚡', keywords: 'admin actividad eventos' });
    }

    function openSearch() {
        overlay.classList.add('abierto');
        setTimeout(function() { input && input.focus(); }, 100);
        if (input) { input.value = ''; doSearch(''); }
    }

    function closeSearch() {
        overlay.classList.remove('abierto');
        if (input) input.blur();
    }

    function doSearch(query) {
        var q = query.toLowerCase().trim();
        if (!q) {
            results.innerHTML = searchRoutes.map(function(r) {
                return '<a href="' + r.url + '" class="search-result-item" onclick="closeSearch"><span class="sr-icon">' + r.icon + '</span><span class="sr-text"><div class="sr-title">' + r.label + '</div><div class="sr-desc">' + r.url + '</div></span><span class="sr-arrow">→</span></a>';
            }).join('');
            return;
        }
        var filtered = searchRoutes.filter(function(r) {
            return r.label.toLowerCase().includes(q) || r.keywords.toLowerCase().includes(q) || r.url.toLowerCase().includes(q);
        });
        if (filtered.length === 0) {
            results.innerHTML = '<div class="search-empty">🔍 No se encontraron resultados para <strong>"' + query + '"</strong></div>';
        } else {
            results.innerHTML = filtered.map(function(r) {
                return '<a href="' + r.url + '" class="search-result-item" onclick="closeSearch"><span class="sr-icon">' + r.icon + '</span><span class="sr-text"><div class="sr-title">' + r.label.replace(new RegExp('(' + q + ')', 'gi'), '<strong style="color:#a78bfa">$1</strong>') + '</div><div class="sr-desc">' + r.url + '</div></span><span class="sr-arrow">→</span></a>';
            }).join('');
        }
    }

    // Close handler
    window.closeSearch = closeSearch;

    // Search results item click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) closeSearch();
    });

    // ESC close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('abierto')) {
            closeSearch();
        }
    });

    // Ctrl+K or Cmd+K open
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
            e.preventDefault();
            openSearch();
        }
        // Ctrl+Shift+F also
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'f' || e.key === 'F')) {
            e.preventDefault();
            openSearch();
        }
    });

    // Input handler
    if (input) {
        input.addEventListener('input', function() { doSearch(this.value); });
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeSearch();
            if (e.key === 'Enter') {
                var first = results.querySelector('.search-result-item');
                if (first) { window.location.href = first.getAttribute('href'); closeSearch(); }
            }
        });
    }

})();

/* ?????????????????????????????????????????

   22. ENHANCED CARD MOUSE TRACK (optimizado)

????????????????????????????????????????? */

(function() {
    var cards = document.querySelectorAll('.kpi-card, .section-card, .chart-card');
    if (cards.length === 0) return;
    var ticking = false;
    cards.forEach(function(card) {
        card.addEventListener('mousemove', function(e) {
            if (!ticking) {
                window.requestAnimationFrame(function() {
                    var rect = card.getBoundingClientRect();
                    var x = ((e.clientX - rect.left) / rect.width * 100).toFixed(1);
                    var y = ((e.clientY - rect.top) / rect.height * 100).toFixed(1);
                    card.style.setProperty('--mx', x + '%');
                    card.style.setProperty('--my', y + '%');
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    });
})();

/* ?????????????????????????????????????????

   23. KEYBOARD SHORTCUTS

????????????????????????????????????????? */

(function() {
    if (window.__shortcutsInited) return;
    window.__shortcutsInited = true;

    var helpBar = document.createElement('div');
    helpBar.className = 'shortcuts-help';
    helpBar.id = 'shortcutsHelp';
    helpBar.innerHTML = '<kbd>N</kbd> Venta <kbd>B</kbd> Compra <kbd>G</kbd> Gasto <kbd>P</kbd> Producto <kbd>K</kbd> Buscar <kbd>F1</kbd> Ayuda';
    document.body.appendChild(helpBar);

    var helpTimeout;
    function showHelp() {
        helpBar.classList.add('show');
        clearTimeout(helpTimeout);
        helpTimeout = setTimeout(function() { helpBar.classList.remove('show'); }, 4000);
    }

    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
        if (e.ctrlKey || e.metaKey) return;
        var key = e.key.toLowerCase();
        var handled = true;
        switch (key) {
            case 'n': window.location.href = '/ventas'; break;
            case 'b': window.location.href = '/blog'; break;
            case 'g': window.location.href = '/gastos'; break;
            case 'p': document.getElementById('formSection')?.scrollIntoView({behavior:'smooth'}); break;
            case 'f1': e.preventDefault(); showHelp(); break;
            default: handled = false;
        }
        if (handled) { e.preventDefault(); showHelp(); }
    });

    showHelp();
})();

/* ?????????????????????????????????????????

   24. PRINT BARCODE LABEL

????????????????????????????????????????? */

window.imprimirEtiqueta = function(id, nombre, precio) {
    var w = window.open('', '_blank', 'width=400,height=300');
    if (!w) { alert('Permite ventanas emergentes para imprimir etiquetas'); return; }
    var html = '<html><head><style>body{margin:0;padding:12px;font-family:Arial,sans-serif;text-align:center}';
    html += '.label{border:1px dashed #ccc;padding:10px;display:inline-block}';
    html += '.name{font-size:12px;font-weight:bold;margin-bottom:4px}';
    html += '.price{font-size:16px;color:#7c3aed;font-weight:800;margin-top:4px}';
    html += '.code{font-size:8px;color:#999;margin-top:2px}';
    html += '@media print{@page{margin:0}body{padding:6px}.label{border:none}}</style></head><body>';
    html += '<div class="label">';
    html += '<div class="name">' + nombre + '</div>';
    html += '<div><svg id="barcode"></svg></div>';
    html += '<div class="price">$' + parseFloat(precio).toLocaleString('es-CO') + '</div>';
    html += '<div class="code">ID: ' + id + '</div>';
    html += '</div>';
    html += '<script src="https://cdnjs.cloudflare.com/ajax/libs/jsbarcode/3.11.5/JsBarcode.all.min.js"><\/script>';
    html += '<script>document.addEventListener("DOMContentLoaded",function(){try{JsBarcode("#barcode","' + id + '",{format:"CODE128",width:1.2,height:30,displayValue:false})}catch(e){}});setTimeout(function(){window.print();window.close()},500);<\/script>';
    html += '</body></html>';
    w.document.write(html);
    w.document.close();
};

/* ?????????????????????????????????????????

   25. HAMBURGUER MENU TOGGLE

????????????????????????????????????????? */

(function() {
    var topbar = document.querySelector('.topbar');
    if (!topbar) return;
    var center = topbar.querySelector('.topbar-center');
    if (!center) return;
    if (topbar.querySelector('.hamburger')) return;

    var btn = document.createElement('button');
    btn.className = 'hamburger';
    btn.setAttribute('aria-label', 'Menu');
    btn.innerHTML = '<span></span><span></span><span></span>';
    btn.style.marginLeft = 'auto';
    topbar.appendChild(btn);

    btn.addEventListener('click', function() {
        btn.classList.toggle('active');
        center.classList.toggle('open');
    });

    document.addEventListener('click', function(e) {
        if (!topbar.contains(e.target)) {
            btn.classList.remove('active');
            center.classList.remove('open');
        }
    });
})();

/* ?????????????????????????????????????????

   26. SKELETON LOADING + GOALS

????????????????????????????????????????? */

(function() {
    var main = document.querySelector('.main');
    if (!main || document.querySelector('.kpi-card')) return;

    var kpiGrid = main.querySelector('.kpi-grid');
    if (kpiGrid && !kpiGrid.querySelector('.skeleton-card')) {
        kpiGrid.innerHTML = '';
        for (var i = 0; i < 8; i++) {
            var sk = document.createElement('div');
            sk.className = 'skeleton skeleton-card';
            sk.style.animationDelay = (i * 0.05) + 's';
            kpiGrid.appendChild(sk);
        }
    }

    var goalCard = document.querySelector('.goal-card');
    if (goalCard) {
        var fill = goalCard.querySelector('.goal-bar-fill');
        if (fill) {
            setTimeout(function() {
                fill.style.width = fill.getAttribute('data-target') || '0%';
            }, 300);
        }
    }
})();

})();


