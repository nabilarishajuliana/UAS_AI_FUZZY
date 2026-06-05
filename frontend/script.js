// frontend/script.js
// =====================================================
// JavaScript untuk FuzzyStock
// Menghubungkan frontend ke Flask API
// =====================================================

const API = 'http://localhost:5000';

// ─── Warna avatar per ticker ─────────────────────────
const AVATAR_COLORS = {
  BBCA: { bg:'#EBF3FC', color:'#2A6FBF', text:'BCA' },
  BBRI: { bg:'#E6F5EF', color:'#0E6B4F', text:'BRI' },
  ASII: { bg:'#FDF4E7', color:'#B87318', text:'ASI' },
  TLKM: { bg:'#FDEEED', color:'#D44848', text:'TLK' },
  GOTO: { bg:'#FDEEED', color:'#D44848', text:'GTO' },
  BMRI: { bg:'#E6F5EF', color:'#0E6B4F', text:'MDR' },
  BREN: { bg:'#E6F5EF', color:'#0E6B4F', text:'BRN' },
  UNVR: { bg:'#EBF3FC', color:'#2A6FBF', text:'UNV' },
};

// ─── Warna rekomendasi ────────────────────────────────
const REC_CFG = {
  'Strong Buy':  { bg:'#E6F5EF', border:'#9FDBC6', color:'#0E6B4F', desc:'RSI oversold + MACD bullish. Momentum kuat untuk masuk posisi beli.', badge:'badge-buy' },
  'Buy':         { bg:'#EEF8F4', border:'#9FDBC6', color:'#1A9B72', desc:'Indikator teknikal menunjukkan sinyal positif untuk masuk posisi.', badge:'badge-buy' },
  'Hold':        { bg:'#FDF7EE', border:'#EDCA8A', color:'#B87318', desc:'Sentimen netral. Tunggu konfirmasi sinyal lebih lanjut.', badge:'badge-hold' },
  'Sell':        { bg:'#FEF4F4', border:'#F5AAAA', color:'#D44848', desc:'Indikator melemah. Pertimbangkan mengurangi posisi.', badge:'badge-sell' },
  'Strong Sell': { bg:'#FDEEED', border:'#F5AAAA', color:'#AE2D2D', desc:'RSI overbought + MACD bearish. Sinyal kuat untuk keluar dari posisi.', badge:'badge-sell' },
};

let STOCK_UNIVERSE = [];

// ─────────────────────────────────────────────────────
// LANDING PAGE FUNCTIONS
// ─────────────────────────────────────────────────────

// Cek apakah kita di landing page atau detail page
const isLanding = document.getElementById('stock-grid') !== null;
const isDetail  = document.getElementById('chart-plotly') !== null;

if (isLanding) {
  setupNavSearch();
  loadLandingPage();
}

if (isDetail) {
  loadDetailPage();
}


// ─── LANDING: Load semua saham ────────────────────────

async function loadLandingPage() {
  try {
    const [stocksRes, universeRes] = await Promise.all([
      fetch(`${API}/api/stocks`),
      fetch(`${API}/api/universe`),
    ]);

    const json = await stocksRes.json();
    const universeJson = await universeRes.json();

    if (json.status !== 'ok') throw new Error('API error');
    if (universeJson.status !== 'ok') throw new Error('Universe API error');

    const stocks = json.data;
    STOCK_UNIVERSE = universeJson.data || [];

    // Render ticker tape
    renderTicker(stocks);

    // Populate search suggestions
    populateSearchOptions(STOCK_UNIVERSE);

    // Render stock grid seperti versi lama
    renderStockGrid(stocks);

  } catch (err) {
    console.error('Error load landing:', err);
    showToast('Gagal memuat data. Pastikan server Flask berjalan.');
    document.getElementById('stock-grid').innerHTML =
      '<p style="color:#D44848;font-size:13px;grid-column:1/-1;text-align:center;padding:2rem;">Gagal memuat data. Pastikan server Flask berjalan di port 5000.</p>';
  }
}


function setupNavSearch() {
  const form = document.getElementById('nav-search-form');
  const input = document.getElementById('nav-search-input');

  if (!form || !input) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    handleStockSearch(input.value);
  });

  input.addEventListener('input', () => {
    if (!input.value.trim()) {
      return;
    }
  });
}


function populateSearchOptions(universe) {
  const list = document.getElementById('stock-search-list');
  if (!list) return;

  list.innerHTML = universe.map(item => `<option value="${item.ticker}"></option>`).join('');
}


function normalizeSearchText(value) {
  return (value || '')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}


function findStockMatches(query) {
  const normalized = normalizeSearchText(query);
  if (!normalized) return [];

  const directTicker = STOCK_UNIVERSE.find(item => item.ticker === normalized);
  if (directTicker) return [directTicker];

  return STOCK_UNIVERSE.filter(item => normalizeSearchText(item.ticker).startsWith(normalized)).slice(0, 12);
}


function handleStockSearch(query) {
  const cleaned = query.trim();

  if (!cleaned) {
    showToast('Masukkan kode saham, misalnya BBCA.');
    return;
  }

  const matches = findStockMatches(cleaned);

  if (matches.length === 0) {
    showToast(`Kode saham "${cleaned}" tidak ditemukan.`);
    return;
  }

  if (matches.length === 1) {
    sessionStorage.setItem('ticker', matches[0].ticker);
    window.location.href = 'detail.html';
    return;
  }

  showToast(`Kode "${cleaned}" terlalu umum. Ketik kode lengkap, misalnya BBCA.`);
}


function renderTicker(stocks) {
  const track = document.getElementById('ticker-track');
  if (!track) return;

  // Buat item ticker dua kali untuk animasi seamless
  let html = '';
  for (let i = 0; i < 2; i++) {
    stocks.forEach(s => {
      const arah  = s.naik ? '▲' : '▼';
      const cls   = s.naik ? 'ti-up' : 'ti-dn';
      const harga = s.harga ? s.harga.toLocaleString('id-ID') : '—';
      html += `<div class="ti">
        <span class="ti-sym">${s.ticker}</span>
        <span class="ti-price">${harga}</span>
        <span class="${cls}">${arah} ${Math.abs(s.perubahan_persen || 0).toFixed(1)}%</span>
      </div>`;
    });
  }
  track.innerHTML = html;
}


function renderStockGrid(stocks) {
  const grid = document.getElementById('stock-grid');
  if (!grid) return;

  grid.innerHTML = stocks.map(s => {
    const av     = AVATAR_COLORS[s.ticker] || { bg:'#F0F3EE', color:'#526050', text:s.ticker.slice(0,3) };
    const cfg    = REC_CFG[s.rekomendasi] || REC_CFG['Hold'];
    const arah   = s.naik ? '▲' : '▼';
    const chgCls = s.naik ? 'c-up' : 'c-dn';
    const harga  = s.harga ? 'Rp ' + s.harga.toLocaleString('id-ID') : '—';
    const pct    = s.perubahan_persen ? Math.abs(s.perubahan_persen).toFixed(2) : '—';
    const recCat = s.rekomendasi?.includes('Buy')  ? 'buy' :
                   s.rekomendasi?.includes('Sell') ? 'sell' : 'hold';
    const vol    = `${Number(s.volume_ratio || 0).toFixed(2)}x`;
    const rsi    = `${Number(s.rsi || 0).toFixed(0)}`;
    const macd   = s.macd_label || '—';

    // Mini chart SVG dari score
    const chartColor = cfg.color;
    const chartSvg   = makeMiniChart(s.rekomendasi, chartColor);

    return `
      <div class="scard" data-rec="${recCat}" onclick="goDetail('${s.ticker}')">
        <div class="scard-top">
          <div class="scard-av" style="background:${av.bg};color:${av.color};">${av.text}</div>
          <span class="badge ${cfg.badge}">${s.rekomendasi || '—'}</span>
        </div>
        <div class="scard-ticker">${s.ticker}</div>
        <div class="scard-name">${s.nama}</div>
        <div class="scard-price">${harga}</div>
        <div class="scard-metrics">
          <span class="metric-pill vol">Vol <strong>${vol}</strong></span>
          <span class="metric-pill rsi">RSI <strong>${rsi}</strong></span>
          <span class="metric-pill macd">MACD <strong>${macd}</strong></span>
        </div>
        <div class="scard-chg ${chgCls}">${arah} ${pct}% hari ini</div>
        ${chartSvg}
      </div>`;
  }).join('');
}


function makeMiniChart(rekomendasi, color) {
  // Generate pola mini chart berdasarkan rekomendasi
  const points = [];
  const n = 8;
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    let y;
    if (rekomendasi?.includes('Strong Buy'))   y = 38 - t * 32;
    else if (rekomendasi?.includes('Buy'))     y = 34 - t * 26;
    else if (rekomendasi?.includes('Strong Sell')) y = 6 + t * 32;
    else if (rekomendasi?.includes('Sell'))    y = 8 + t * 26;
    else y = 20 + Math.sin(t * Math.PI * 2) * 8;

    y += (Math.random() - 0.5) * 6;
    y = Math.max(2, Math.min(38, y));
    points.push(`${(t * 150).toFixed(0)},${y.toFixed(0)}`);
  }

  const pStr = points.join(' ');
  const fill = pStr + ' 150,40 0,40';

  return `<svg class="scard-chart" viewBox="0 0 150 40" preserveAspectRatio="none">
    <polygon points="${fill}" fill="${color}22"/>
    <polyline points="${pStr}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round"/>
  </svg>`;
}


function doFilter(btn, type) {
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('on'));
  btn.classList.add('on');
  document.querySelectorAll('.scard').forEach(c => {
    c.style.display = type === 'all' || c.dataset.rec === type ? '' : 'none';
  });
}


function goDetail(ticker) {
  // Simpan ticker ke sessionStorage lalu pindah ke detail.html
  sessionStorage.setItem('ticker', ticker);
  window.location.href = 'detail.html';
}


function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}


// ─────────────────────────────────────────────────────
// DETAIL PAGE FUNCTIONS
// ─────────────────────────────────────────────────────

async function loadDetailPage() {
  // Ambil ticker dari sessionStorage
  const ticker = sessionStorage.getItem('ticker') || 'BBCA';

  document.getElementById('nav-ticker').textContent = ticker;
  document.getElementById('nav-name').textContent   = 'Memuat data...';

  try {
    const res  = await fetch(`${API}/api/analyze/${ticker}`);
    const json = await res.json();

    if (json.status !== 'ok') throw new Error(json.pesan || 'API error');

    const d = json.data;
    renderDetail(d);

  } catch (err) {
    console.error('Error load detail:', err);
    document.getElementById('loading-state').innerHTML =
      `<p style="color:#D44848;font-size:14px;text-align:center;">Gagal memuat data ${ticker}.<br/>Pastikan server Flask berjalan.</p>`;
  }
}


function renderDetail(d) {
  const cfg = REC_CFG[d.rekomendasi] || REC_CFG['Hold'];
  const isUp = d.naik;

  // Sembunyikan loading, tampilkan konten
  document.getElementById('loading-state').style.display = 'none';
  document.getElementById('main-content').style.display  = 'block';

  // ── Navbar ─────────────────────────────────────────
  document.getElementById('nav-ticker').textContent = d.ticker;
  document.getElementById('nav-name').textContent   = d.nama;

  // ── Hero ───────────────────────────────────────────
  document.getElementById('d-price').textContent =
    'Rp ' + (d.harga || 0).toLocaleString('id-ID');

  const chgEl = document.getElementById('d-chg');
  const arah  = isUp ? '▲' : '▼';
  chgEl.textContent  = `${arah} ${Math.abs(d.perubahan_persen || 0).toFixed(2)}% hari ini`;
  chgEl.style.cssText = `display:inline-flex;align-items:center;gap:4px;font-family:var(--mono);font-size:12px;font-weight:500;padding:4px 13px;border-radius:20px;margin-top:10px;background:${isUp?'#E6F5EF':'#FDEEED'};color:${isUp?'#0E6B4F':'#D44848'};`;

  document.getElementById('d-rsi-meta').textContent  = `${d.rsi} (${d.rsi_label})`;
  document.getElementById('d-macd-meta').textContent = d.macd_label;
  document.getElementById('d-vol-meta').textContent  = `${d.volume_ratio}x (${d.vol_label})`;

  // Score pill
  const pill = document.getElementById('d-score-pill');
  pill.style.background   = cfg.bg;
  pill.style.borderColor  = cfg.border;
  pill.style.color        = cfg.color;
  document.getElementById('d-sp-num').textContent = d.score;
  document.getElementById('d-sp-rec').textContent = d.rekomendasi;

  // ── Grafik Plotly ───────────────────────────────────
  renderChart(d.chart, d.rekomendasi, cfg.color);
  renderIndicatorCharts(d.chart);

  // ── RSI indicator ───────────────────────────────────
  document.getElementById('d-rsi-val').textContent = d.rsi;
  const rsiColor = d.rsi < 30 ? '#1A9B72' : d.rsi > 70 ? '#D44848' : '#B87318';
  const rsiBg    = d.rsi < 30 ? '#E6F5EF' : d.rsi > 70 ? '#FDEEED' : '#FDF4E7';
  const rsiBrd   = d.rsi < 30 ? '#9FDBC6' : d.rsi > 70 ? '#F5AAAA' : '#EDCA8A';
  document.getElementById('d-rsi-bar').style.width      = Math.min(d.rsi, 100) + '%';
  document.getElementById('d-rsi-bar').style.background = rsiColor;
  const rsiBadge = document.getElementById('d-rsi-badge');
  rsiBadge.textContent = d.rsi_label;
  rsiBadge.style.cssText = `font-family:var(--mono);font-size:10px;font-weight:500;padding:3px 10px;border-radius:20px;background:${rsiBg};color:${rsiColor};border:1px solid ${rsiBrd};`;

  // ── MACD indicator ──────────────────────────────────
  document.getElementById('d-macd-val').textContent = d.macd_normalized >= 0 ? `+${d.macd_normalized.toFixed(4)}` : d.macd_normalized.toFixed(4);
  const macdColor = d.macd_label === 'Bullish' ? '#1A9B72' : d.macd_label === 'Bearish' ? '#D44848' : '#B87318';
  const macdBg    = d.macd_label === 'Bullish' ? '#E6F5EF' : d.macd_label === 'Bearish' ? '#FDEEED' : '#FDF4E7';
  const macdBrd   = d.macd_label === 'Bullish' ? '#9FDBC6' : d.macd_label === 'Bearish' ? '#F5AAAA' : '#EDCA8A';
  const mn = d.macd_normalized || 0;
  const mfill = document.getElementById('d-macd-bar');
  mfill.style.background = macdColor;
  mfill.style.left  = mn >= 0 ? '50%' : (50 + mn * 25) + '%';
  mfill.style.width = Math.abs(mn) * 25 + '%';
  const macdBadge = document.getElementById('d-macd-badge');
  macdBadge.textContent = d.macd_label;
  macdBadge.style.cssText = `font-family:var(--mono);font-size:10px;font-weight:500;padding:3px 10px;border-radius:20px;background:${macdBg};color:${macdColor};border:1px solid ${macdBrd};`;

  // ── Volume badge ────────────────────────────────────
  const volColor = d.vol_label === 'High' ? '#1A9B72' : d.vol_label === 'Low' ? '#2A6FBF' : '#B87318';
  const volBg    = d.vol_label === 'High' ? '#E6F5EF' : d.vol_label === 'Low' ? '#EBF3FC' : '#FDF4E7';
  const volBrd   = d.vol_label === 'High' ? '#9FDBC6' : d.vol_label === 'Low' ? '#A3C4EE' : '#EDCA8A';
  const volBadge = document.getElementById('d-vol-badge');
  volBadge.textContent = `${d.volume_ratio}x · ${d.vol_label}`;
  volBadge.style.cssText = `font-family:var(--mono);font-size:10px;font-weight:500;padding:3px 10px;border-radius:20px;background:${volBg};color:${volColor};border:1px solid ${volBrd};`;

  // ── Score bar ───────────────────────────────────────
  document.getElementById('d-score-big').textContent  = d.score;
  document.getElementById('d-score-big').style.color  = cfg.color;
  document.getElementById('d-sbar').style.width       = d.score + '%';
  document.getElementById('d-sbar').style.background  = cfg.color;

  // ── Rec banner ──────────────────────────────────────
  const rb = document.getElementById('d-rec-block');
  rb.style.background  = cfg.bg;
  rb.style.borderColor = cfg.border;
  rb.style.color       = cfg.color;
  document.getElementById('d-rec-name').textContent = d.rekomendasi;
  document.getElementById('d-rec-desc').textContent = cfg.desc;
  document.getElementById('d-rec-icon').style.background = cfg.bg;

  // ── Rules aktif ─────────────────────────────────────
  const rulesEl = document.getElementById('d-rules');
  if (d.rules_aktif && d.rules_aktif.length > 0) {
    rulesEl.innerHTML = d.rules_aktif.map(r => `
      <div class="rule-item">
        <div class="rule-dot"></div>
        <span class="rule-text">IF <strong>${r.rule.replace(/AND/g, '</strong> AND <strong>').replace(/THEN/g, '</strong> THEN <strong>')}  </strong></span>
        <span class="rule-alpha">α = ${r.alpha}</span>
      </div>`).join('');
  } else {
    rulesEl.innerHTML = '<p style="font-size:12px;color:var(--text3);">Tidak ada rule yang aktif signifikan.</p>';
  }

  // ── Detail Fuzzifikasi ──────────────────────────────
  if (d.fuzzifikasi) {
    renderFuzzifikasi(d.fuzzifikasi);
  }

  // ── MF Marker ───────────────────────────────────────
  const mfLine = document.getElementById('mf-line');
  const mfDot = document.getElementById('mf-dot');
  const mfLabelBg = document.getElementById('mf-label-bg');
  const mfLabel = document.getElementById('mf-label');
  if (mfLine && mfDot && mfLabelBg && mfLabel) {
    const mx = 20 + (Math.min(d.rsi, 100) / 100) * 780;
    mfLine.setAttribute('x1', mx.toFixed(1));
    mfLine.setAttribute('x2', mx.toFixed(1));
    mfDot.setAttribute('cx', mx.toFixed(1));
    mfLabelBg.setAttribute('x', (mx + 5).toFixed(1));
    mfLabel.setAttribute('x', (mx + 44).toFixed(1));
    mfLabel.textContent = `RSI = ${d.rsi}`;
  }
}


function renderChart(chartData, rekomendasi, color) {
  if (!chartData || chartData.length === 0) return;

  const tanggal = chartData.map(c => c.tanggal);
  const close   = chartData.map(c => c.close);

  const trace = {
    x: tanggal,
    y: close,
    type: 'scatter',
    mode: 'lines',
    name: 'Harga Close',
    line: { color: color, width: 2 },
    fill: 'tozeroy',
    fillcolor: color + '18',
  };

  const layout = {
    margin: { t: 10, r: 10, b: 40, l: 60 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'DM Mono, monospace', size: 11, color: '#96A492' },
    xaxis: {
      gridcolor: '#F0F3EE',
      showgrid: true,
      zeroline: false,
    },
    yaxis: {
      gridcolor: '#F0F3EE',
      showgrid: true,
      zeroline: false,
      tickformat: ',.0f',
    },
    showlegend: false,
    hovermode: 'x unified',
  };

  Plotly.newPlot('chart-plotly', [trace], layout, {
    responsive: true,
    displayModeBar: false,
  });
}


function calculateEmaSeries(values, period) {
  if (!values || values.length === 0) return [];

  const multiplier = 2 / (period + 1);
  const series = [];
  let ema = values[0];

  values.forEach((value, index) => {
    if (index === 0) {
      ema = value;
    } else {
      ema = ((value - ema) * multiplier) + ema;
    }
    series.push(ema);
  });

  return series;
}


function calculateMovingAverageSeries(values, period) {
  if (!values || values.length === 0) return [];

  return values.map((_, index) => {
    if (index + 1 < period) return null;
    const start = index + 1 - period;
    const chunk = values.slice(start, index + 1);
    const sum = chunk.reduce((acc, value) => acc + value, 0);
    return sum / period;
  });
}


function calculateRsiSeries(values, period = 14) {
  const series = new Array(values.length).fill(null);
  if (values.length <= period) return series;

  let gainSum = 0;
  let lossSum = 0;

  for (let i = 1; i <= period; i++) {
    const delta = values[i] - values[i - 1];
    if (delta >= 0) {
      gainSum += delta;
    } else {
      lossSum += Math.abs(delta);
    }
  }

  let avgGain = gainSum / period;
  let avgLoss = lossSum / period;
  series[period] = avgLoss === 0 ? 100 : 100 - (100 / (1 + (avgGain / avgLoss)));

  for (let i = period + 1; i < values.length; i++) {
    const delta = values[i] - values[i - 1];
    const gain = Math.max(delta, 0);
    const loss = Math.max(-delta, 0);

    avgGain = ((avgGain * (period - 1)) + gain) / period;
    avgLoss = ((avgLoss * (period - 1)) + loss) / period;

    series[i] = avgLoss === 0 ? 100 : 100 - (100 / (1 + (avgGain / avgLoss)));
  }

  return series;
}


function renderIndicatorCharts(chartData) {
  if (!chartData || chartData.length < 2) return;

  const tanggal = chartData.map(c => c.tanggal);
  const close   = chartData.map(c => c.close);
  const volume  = chartData.map(c => c.volume);

  const volumeMa = calculateMovingAverageSeries(volume, 20);
  const rsiSeries = calculateRsiSeries(close, 14);

  const ema12 = calculateEmaSeries(close, 12);
  const ema26 = calculateEmaSeries(close, 26);
  const macdLine = close.map((_, index) => ema12[index] - ema26[index]);
  const signalLine = calculateEmaSeries(macdLine, 9);
  const histogram = macdLine.map((value, index) => value - signalLine[index]);

  const commonLayout = {
    margin: { t: 6, r: 6, b: 28, l: 42 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'DM Mono, monospace', size: 10, color: '#96A492' },
    showlegend: false,
    hovermode: 'x unified',
    xaxis: {
      gridcolor: '#F0F3EE',
      showgrid: true,
      zeroline: false,
      tickfont: { size: 9 },
    },
  };

  Plotly.newPlot('volume-plotly', [
    {
      x: tanggal,
      y: volume,
      type: 'bar',
      marker: { color: '#1A9B7250' },
      hovertemplate: '%{x}<br>Volume: %{y:,}<extra></extra>',
    },
    {
      x: tanggal,
      y: volumeMa,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#B87318', width: 2 },
      hovertemplate: '%{x}<br>MA20: %{y:,.0f}<extra></extra>',
    },
  ], {
    ...commonLayout,
    yaxis: {
      gridcolor: '#F0F3EE',
      showgrid: true,
      zeroline: false,
      tickformat: ',.2s',
    },
  }, {
    responsive: true,
    displayModeBar: false,
  });

  Plotly.newPlot('rsi-plotly', [
    {
      x: tanggal,
      y: rsiSeries,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#1A9B72', width: 2 },
      fill: 'tozeroy',
      fillcolor: '#1A9B7214',
      hovertemplate: '%{x}<br>RSI: %{y:.2f}<extra></extra>',
    },
  ], {
    ...commonLayout,
    yaxis: {
      range: [0, 100],
      gridcolor: '#F0F3EE',
      showgrid: true,
      zeroline: false,
      tickvals: [0, 30, 50, 70, 100],
    },
    shapes: [
      { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 30, y1: 30, line: { color: '#D44848', width: 1, dash: 'dot' } },
      { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 70, y1: 70, line: { color: '#1A9B72', width: 1, dash: 'dot' } },
    ],
  }, {
    responsive: true,
    displayModeBar: false,
  });

  const macdColors = histogram.map(v => (v >= 0 ? '#1A9B72' : '#D44848'));

  Plotly.newPlot('macd-plotly', [
    {
      x: tanggal,
      y: histogram,
      type: 'bar',
      marker: { color: macdColors },
      hovertemplate: '%{x}<br>Histogram: %{y:.4f}<extra></extra>',
    },
    {
      x: tanggal,
      y: macdLine,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#0E6B4F', width: 2 },
      hovertemplate: '%{x}<br>MACD: %{y:.4f}<extra></extra>',
    },
    {
      x: tanggal,
      y: signalLine,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#B87318', width: 2 },
      hovertemplate: '%{x}<br>Signal: %{y:.4f}<extra></extra>',
    },
  ], {
    ...commonLayout,
    yaxis: {
      gridcolor: '#F0F3EE',
      showgrid: true,
      zeroline: false,
      tickformat: '.2f',
    },
    shapes: [
      { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 0, y1: 0, line: { color: '#96A492', width: 1, dash: 'dot' } },
    ],
  }, {
    responsive: true,
    displayModeBar: false,
  });
}


function renderFuzzifikasi(fuzz) {
  const grid = document.getElementById('d-fuzz-grid');
  if (!grid) return;

  const sections = [
    { title: 'RSI', data: fuzz.rsi,    items: [
      { label: 'Oversold',   val: fuzz.rsi?.oversold,   color: '#D44848' },
      { label: 'Neutral',    val: fuzz.rsi?.neutral,    color: '#B87318' },
      { label: 'Overbought', val: fuzz.rsi?.overbought, color: '#1A9B72' },
    ]},
    { title: 'MACD', data: fuzz.macd,  items: [
      { label: 'Bearish',  val: fuzz.macd?.bearish,  color: '#D44848' },
      { label: 'Sideways', val: fuzz.macd?.sideways, color: '#B87318' },
      { label: 'Bullish',  val: fuzz.macd?.bullish,  color: '#1A9B72' },
    ]},
    { title: 'Volume', data: fuzz.volume, items: [
      { label: 'Low',     val: fuzz.volume?.low,     color: '#2A6FBF' },
      { label: 'Average', val: fuzz.volume?.average, color: '#B87318' },
      { label: 'High',    val: fuzz.volume?.high,    color: '#1A9B72' },
    ]},
  ];

  grid.innerHTML = sections.map(sec => `
    <div class="fuzz-cell">
      <div class="fuzz-cell-title">${sec.title}</div>
      ${sec.items.map(item => {
        const pct = Math.round((item.val || 0) * 100);
        return `
          <div class="fuzz-row">
            <span class="fuzz-label">${item.label}</span>
            <span class="fuzz-val" style="color:${pct > 0 ? item.color : '#96A492'}">${(item.val || 0).toFixed(3)}</span>
          </div>
          <div class="fuzz-bar">
            <div class="fuzz-bar-fill" style="width:${pct}%;background:${item.color};"></div>
          </div>`;
      }).join('')}
    </div>`).join('');
}