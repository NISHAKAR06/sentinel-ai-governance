/**
 * analytics.js — All 5 GET /api/v1/analytics/* endpoints with Chart.js
 */
const AnalyticsPage = (() => {
  let period = '30d';
  const charts = {};

  const _d = () => {
    const dark = document.documentElement.dataset.theme === 'dark';
    return { grid: dark?'rgba(255,255,255,0.06)':'rgba(0,0,0,0.06)', text: dark?'#94A3B8':'#64748B', bg: dark?'#1E293B':'#FFFFFF', border: dark?'#334155':'#E2E8F0' };
  };

  function _destroyAll() { Object.values(charts).forEach(c => c?.destroy()); Object.keys(charts).forEach(k => delete charts[k]); }

  /* ── KPI cards ───────────────────────────────────────────── */
  function _kpis(data) {
    const set = (id, val, trend) => {
      const el = document.getElementById(id); if (!el) return;
      const v = el.querySelector('.kpi-value'), t = el.querySelector('.kpi-trend');
      if (v) v.textContent = val ?? '—';
      if (t && trend != null) {
        const up = trend >= 0;
        t.className = `kpi-trend ${up?'trend-up':'trend-down'}`;
        t.innerHTML = `<i class="fa-solid fa-arrow-${up?'up':'down'}"></i> ${Math.abs(trend)}%`;
      }
    };
    set('kpi-total',      data.total_actions, data.total_trend);
    set('kpi-auto',       data.auto_approved, data.auto_trend);
    set('kpi-reviewed',   data.human_reviewed, null);
    set('kpi-rejected',   data.rejected, null);
    set('kpi-avg-risk',   `${data.avg_risk ?? 0}%`, data.risk_trend);
    set('kpi-compliance', `${data.compliance_rate ?? 0}%`, data.compliance_trend);
  }

  /* ── Daily requests chart ────────────────────────────────── */
  function _daily(data) {
    const ctx = document.getElementById('daily-requests-chart'); if (!ctx) return;
    charts.daily?.destroy();
    const d = _d();
    charts.daily = new Chart(ctx, {
      type: 'line',
      data: { labels: data.labels||[], datasets: [
        { label:'Total', data:data.total||[], borderColor:'#2563EB', backgroundColor:'rgba(37,99,235,0.08)', fill:true, tension:0.4, pointRadius:3, borderWidth:2 },
        { label:'Auto Approved', data:data.auto||[], borderColor:'#16A34A', backgroundColor:'transparent', tension:0.4, pointRadius:3, borderWidth:2, borderDash:[4,4] },
      ]},
      options: { responsive:true, maintainAspectRatio:false,
        interaction:{mode:'index',intersect:false},
        plugins:{legend:{position:'top',labels:{color:d.text,boxWidth:12,padding:16,font:{size:12}}},tooltip:{backgroundColor:d.bg,borderColor:d.border,borderWidth:1,titleColor:d.text,bodyColor:d.text}},
        scales:{x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11},maxRotation:0}},y:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}},beginAtZero:true}},
      },
    });
  }

  /* ── Risk donut ──────────────────────────────────────────── */
  function _risk(data) {
    const ctx = document.getElementById('risk-distribution-chart'); if (!ctx) return;
    charts.risk?.destroy();
    const total = (data.low||0)+(data.medium||0)+(data.high||0)+(data.critical||0);
    const d = _d();
    charts.risk = new Chart(ctx, {
      type:'doughnut',
      data:{ labels:['Low','Medium','High','Critical'], datasets:[{ data:[data.low,data.medium,data.high,data.critical], backgroundColor:['#16A34A','#F59E0B','#DC2626','#7C3AED'], borderColor:d.bg, borderWidth:3, hoverOffset:6 }] },
      options:{ responsive:true, maintainAspectRatio:false, cutout:'70%',
        plugins:{legend:{position:'bottom',labels:{color:d.text,boxWidth:10,padding:12,font:{size:11}}},
          tooltip:{backgroundColor:d.bg,borderColor:d.border,borderWidth:1,titleColor:d.text,bodyColor:d.text,
            callbacks:{label:ctx=>`${ctx.parsed} (${total?Math.round(ctx.parsed/total*100):0}%)`}}},
      },
    });
    const center = document.getElementById('risk-donut-center');
    if (center) center.textContent = total;
  }

  /* ── Approval stacked bar ────────────────────────────────── */
  function _approval(data) {
    const ctx = document.getElementById('approval-rate-chart'); if (!ctx) return;
    charts.approval?.destroy();
    const d = _d();
    charts.approval = new Chart(ctx, {
      type:'bar',
      data:{ labels:data.labels||[], datasets:[
        {label:'Auto Approved', data:data.auto||[], backgroundColor:'rgba(37,99,235,0.80)', borderRadius:4, borderSkipped:false},
        {label:'Human Reviewed', data:data.reviewed||[], backgroundColor:'rgba(245,158,11,0.75)', borderRadius:4, borderSkipped:false},
        {label:'Rejected', data:data.rejected||[], backgroundColor:'rgba(220,38,38,0.70)', borderRadius:4, borderSkipped:false},
      ]},
      options:{ responsive:true, maintainAspectRatio:false,
        plugins:{legend:{position:'top',labels:{color:d.text,boxWidth:12,padding:16,font:{size:12}}},tooltip:{backgroundColor:d.bg,borderColor:d.border,borderWidth:1,titleColor:d.text,bodyColor:d.text}},
        scales:{x:{stacked:true,grid:{color:d.grid},ticks:{color:d.text,font:{size:11}}},y:{stacked:true,grid:{color:d.grid},ticks:{color:d.text,font:{size:11}},beginAtZero:true}},
      },
    });
  }

  /* ── Top operations bar ──────────────────────────────────── */
  function _ops(data) {
    const ctx = document.getElementById('operations-chart'); if (!ctx) return;
    charts.ops?.destroy();
    const d = _d();
    charts.ops = new Chart(ctx, {
      type:'bar',
      data:{ labels:data.labels||[], datasets:[{data:data.counts||[], backgroundColor:'rgba(37,99,235,0.75)', borderRadius:4}] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{legend:{display:false},tooltip:{backgroundColor:d.bg,borderColor:d.border,borderWidth:1,titleColor:d.text,bodyColor:d.text}},
        scales:{x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}},beginAtZero:true},y:{grid:{display:false},ticks:{color:d.text,font:{size:12,weight:'500'}}}},
      },
    });
  }

  /* ── Adaptive learning trend ─────────────────────────────── */
  function _trend(data) {
    const ctx = document.getElementById('learning-trend-chart'); if (!ctx) return;
    charts.learning?.destroy();
    const d = _d();
    charts.learning = new Chart(ctx, {
      type:'line',
      data:{ labels:data.labels||[], datasets:[
        {label:'Auto-Approve Rate (%)', data:data.auto_rate||[], borderColor:'#2563EB', backgroundColor:'rgba(37,99,235,0.10)', fill:true, tension:0.5, pointRadius:4, borderWidth:2},
        {label:'Avg Risk Score', data:data.avg_risk||[], borderColor:'#F59E0B', backgroundColor:'transparent', tension:0.5, pointRadius:4, borderWidth:2, yAxisID:'y1'},
      ]},
      options:{ responsive:true, maintainAspectRatio:false,
        interaction:{mode:'index',intersect:false},
        plugins:{legend:{position:'top',labels:{color:d.text,boxWidth:12,padding:16,font:{size:12}}},tooltip:{backgroundColor:d.bg,borderColor:d.border,borderWidth:1,titleColor:d.text,bodyColor:d.text}},
        scales:{x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}}},y:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}},position:'left',beginAtZero:true,max:100},y1:{grid:{display:false},ticks:{color:d.text,font:{size:11}},position:'right',beginAtZero:true,max:100}},
      },
    });
  }

  /* ── Load all ────────────────────────────────────────────── */
  async function loadAll(p = period) {
    period = p;
    try {
      const [summary, daily, riskDist, ops, trend] = await Promise.all([
        SentinelAPI.analytics.summary(p),
        SentinelAPI.analytics.daily(p),
        SentinelAPI.analytics.risk(p),
        SentinelAPI.analytics.operations(p),
        SentinelAPI.analytics.trend(p),
      ]);
      _kpis(summary);
      _daily(daily);
      _risk(riskDist);
      _approval(daily);  // daily has auto/reviewed/rejected breakdowns
      _ops(ops);
      _trend(trend);
    } catch (e) {
      console.error('[Analytics]', e.message);
    }
  }

  document.addEventListener('themechange', () => { _destroyAll(); loadAll(); });

  function init() {
    document.querySelectorAll('.period-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        _destroyAll();
        loadAll(btn.dataset.period);
      });
    });
    document.getElementById('export-report-btn')?.addEventListener('click', () => {
      SentinelAPI.downloadFile(`/api/v1/analytics/export?period=${period}`, `analytics_report_${period}.csv`).catch(() => {});
    });
    loadAll();
  }

  document.addEventListener('DOMContentLoaded', init);
  return { init, loadAll };
})();
