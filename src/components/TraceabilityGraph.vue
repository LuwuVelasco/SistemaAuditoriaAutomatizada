<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { getGraph } from '@/api/index'

const props = defineProps({
  auditId: { type: String, required: true }
})

const svgRef        = ref(null)
const containerRef  = ref(null)
const loading       = ref(true)
const error         = ref(null)
const graphData     = ref(null)
const tooltip       = ref({ visible: false, x: 0, y: 0, node: null })
const selectedNode  = ref(null)
const filterFramework = ref('all')  // 'all' | 'COBIT' | 'COSO' | 'RGSI'
const showRelated   = ref(true)     // mostrar/ocultar aristas finding-related

let simulation     = null
let svgSelection   = null
let nodeGroup      = null
let linkSelection  = null
let resizeObserver = null

const stats = ref({
  total_norms: 0, total_findings: 0, documents_linked: 0,
  related_findings: 0, cobit_norms: 0, coso_norms: 0, rgsi_norms: 0,
})

const exporting       = ref(null)  // null | 'png' | 'pdf' | 'json'
const showExportMenu  = ref(false)
const exportWrapperRef = ref(null)

// ── API ───────────────────────────────────────────────────────────────────────
async function loadGraph() {
  loading.value = true
  error.value   = null
  try {
    const data    = await getGraph(props.auditId)
    graphData.value = data
    stats.value   = data.stats || stats.value
    await nextTick()
    renderGraph(data)
  } catch (e) {
    console.error('Error cargando grafo:', e)
    error.value = 'No se pudo cargar el mapa de trazabilidad.'
  } finally {
    loading.value = false
  }
}

// ── Renderizado D3 ────────────────────────────────────────────────────────────
function renderGraph(data) {
  if (!svgRef.value) return
  if (simulation) simulation.stop()
  d3.select(svgRef.value).selectAll('*').remove()

  const W = containerRef.value?.clientWidth  || 960
  const H = containerRef.value?.clientHeight || 640

  svgSelection = d3.select(svgRef.value)
    .attr('width', W).attr('height', H)

  // ── Marcadores de flecha ──────────────────────────────────────────────────
  const defs = svgSelection.append('defs')
  const markers = [
    { id: 'arrow-fw',      color: '#6b7280', refX: 28 },
    { id: 'arrow-norm',    color: '#4b5563', refX: 22 },
    { id: 'arrow-doc',     color: '#374151', refX: 22 },
    { id: 'arrow-related', color: '#818cf8', refX: 22 },
  ]
  markers.forEach(({ id, color, refX }) => {
    defs.append('marker')
      .attr('id', id)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', refX).attr('refY', 0)
      .attr('markerWidth', 5).attr('markerHeight', 5)
      .attr('orient', 'auto')
      .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', color)
  })

  // ── Filtrar nodos/aristas ─────────────────────────────────────────────────
  let nodes = data.nodes.map(n => ({ ...n }))
  let edges = data.edges.map(e => ({ ...e }))

  // Filtro de framework
  if (filterFramework.value !== 'all') {
    const fw = filterFramework.value
    const keepIds = new Set()
    // Siempre mostrar el hub del fw seleccionado
    keepIds.add(`fw-${fw}`)
    // Normas de ese fw
    nodes.filter(n => n.type === 'norm' && n.framework === fw).forEach(n => keepIds.add(n.id))
    // Hallazgos conectados a esas normas
    edges.forEach(e => {
      const src = e.source?.id || e.source
      const tgt = e.target?.id || e.target
      if (keepIds.has(src) && e.type === 'norm-finding') keepIds.add(tgt)
    })
    // Documentos conectados a esos hallazgos
    edges.forEach(e => {
      const src = e.source?.id || e.source
      const tgt = e.target?.id || e.target
      if (keepIds.has(src) && e.type === 'finding-doc') keepIds.add(tgt)
    })
    nodes = nodes.filter(n => keepIds.has(n.id))
    edges = edges.filter(e => {
      const src = e.source?.id || e.source
      const tgt = e.target?.id || e.target
      return keepIds.has(src) && keepIds.has(tgt)
    })
  }

  // Ocultar aristas finding-related si el usuario lo desactiva
  if (!showRelated.value) {
    edges = edges.filter(e => e.type !== 'finding-related')
  }

  // ── Zoom ──────────────────────────────────────────────────────────────────
  const zoomGroup = svgSelection.append('g').attr('class', 'zoom-layer')
  svgSelection.call(
    d3.zoom().scaleExtent([0.15, 5])
      .on('zoom', ev => zoomGroup.attr('transform', ev.transform))
  )

  // ── Simulación de fuerzas ─────────────────────────────────────────────────
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id)
      .distance(d => {
        if (d.type === 'fw-norm')        return 140
        if (d.type === 'norm-finding')   return 120
        if (d.type === 'finding-doc')    return 100
        if (d.type === 'finding-related') return 80
        return 110
      })
      .strength(d => d.type === 'finding-related' ? 0.15 : 0.5)
    )
    .force('charge', d3.forceManyBody().strength(d => {
      if (d.type === 'framework') return -600
      if (d.type === 'norm')      return -250
      return -180
    }))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide(d => nodeRadius(d) + 10))

  // ── Links ─────────────────────────────────────────────────────────────────
  linkSelection = zoomGroup.append('g').attr('class', 'links')
    .selectAll('line').data(edges).join('line')
    .attr('class', d => `edge edge-${d.type}`)
    .attr('stroke', d => {
      if (d.type === 'fw-norm')          return d.source?.color || '#6b7280'
      if (d.type === 'norm-finding')     return '#4b5563'
      if (d.type === 'finding-doc')      return '#374151'
      if (d.type === 'finding-related')  return '#6366f1'
      return '#4b5563'
    })
    .attr('stroke-width', d => {
      if (d.type === 'fw-norm')          return 2
      if (d.type === 'finding-related')  return 1.5
      return 1.2
    })
    .attr('stroke-dasharray', d => d.type === 'finding-related' ? '5,3' : null)
    .attr('stroke-opacity', d => d.type === 'finding-related' ? 0.55 : 0.5)
    .attr('marker-end', d => {
      if (d.type === 'fw-norm')          return 'url(#arrow-fw)'
      if (d.type === 'finding-related')  return 'url(#arrow-related)'
      if (d.type === 'finding-doc')      return 'url(#arrow-doc)'
      return 'url(#arrow-norm)'
    })

  // ── Nodos ──────────────────────────────────────────────────────────────────
  nodeGroup = zoomGroup.append('g').attr('class', 'nodes')
    .selectAll('g').data(nodes).join('g')
    .attr('class', d => `graph-node node-${d.type}`)
    .call(
      d3.drag()
        .on('start', (ev, d) => { if (!ev.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y })
        .on('end',   (ev, d) => { if (!ev.active) simulation.alphaTarget(0); d.fx = null; d.fy = null })
    )
    .on('mouseover', (ev, d) => { tooltip.value = { visible: true, x: ev.clientX + 14, y: ev.clientY - 14, node: d } })
    .on('mousemove', (ev)    => { tooltip.value.x = ev.clientX + 14; tooltip.value.y = ev.clientY - 14 })
    .on('mouseout',  ()      => { tooltip.value.visible = false })
    .on('click', (ev, d) => {
      ev.stopPropagation()
      if (selectedNode.value?.id === d.id) {
        selectedNode.value = null
        resetHighlight()
      } else {
        selectedNode.value = d
        highlightNeighbors(d.id, nodes, edges)
      }
    })

  svgSelection.on('click', () => { selectedNode.value = null; resetHighlight() })

  // Círculo externo (glow para frameworks)
  nodeGroup.filter(d => d.type === 'framework')
    .append('circle')
    .attr('r', d => nodeRadius(d) + 8)
    .attr('fill', d => d.color)
    .attr('opacity', 0.12)

  // Círculo principal
  nodeGroup.append('circle')
    .attr('r', nodeRadius)
    .attr('fill', d => d.color || '#6b7280')
    .attr('stroke', d => {
      if (d.type === 'framework') return d.color
      return 'rgba(255,255,255,0.1)'
    })
    .attr('stroke-width', d => d.type === 'framework' ? 2.5 : 1)

  // Texto dentro del nodo
  nodeGroup.append('text')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'central')
    .attr('font-size', d => {
      if (d.type === 'framework') return '11px'
      if (d.type === 'norm')      return '8px'
      return '11px'
    })
    .attr('font-weight', d => d.type === 'framework' ? '700' : '400')
    .attr('fill', '#fff')
    .attr('pointer-events', 'none')
    .text(d => nodeIcon(d))

  // Etiqueta exterior
  nodeGroup.append('text')
    .attr('text-anchor', 'middle')
    .attr('y', d => nodeRadius(d) + 13)
    .attr('font-size', d => d.type === 'framework' ? '10px' : '9px')
    .attr('font-weight', d => d.type === 'framework' ? '600' : '400')
    .attr('font-family', 'Inter, sans-serif')
    .attr('fill', d => d.type === 'framework' ? d.color : '#9ca3af')
    .attr('pointer-events', 'none')
    .text(d => {
      if (d.type === 'framework') return d.label
      return truncate(d.label, 13)
    })

  // ── Tick ──────────────────────────────────────────────────────────────────
  simulation.on('tick', () => {
    linkSelection
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`)
  })
}

// ── Utilidades ────────────────────────────────────────────────────────────────
function nodeRadius(d) {
  if (d.type === 'framework') return 26
  if (d.type === 'norm')      return 13
  if (d.type === 'finding')   return 16
  if (d.type === 'document')  return 12
  return 12
}

function nodeIcon(d) {
  if (d.type === 'framework') return d.label
  if (d.type === 'norm') {
    if (d.framework === 'COBIT') return 'C'
    if (d.framework === 'COSO')  return 'S'
    if (d.framework === 'RGSI')  return 'R'
  }
  if (d.type === 'finding')  return '⚑'
  if (d.type === 'document') return '📄'
  return '?'
}

function truncate(s, max) {
  return s && s.length > max ? s.slice(0, max) + '…' : (s || '')
}

function highlightNeighbors(nodeId, nodes, edges) {
  const linked = new Set([nodeId])
  edges.forEach(e => {
    const s = e.source?.id || e.source
    const t = e.target?.id || e.target
    if (s === nodeId) linked.add(t)
    if (t === nodeId) linked.add(s)
  })
  nodeGroup.attr('opacity', d => linked.has(d.id) ? 1 : 0.1)
  linkSelection.attr('opacity', e => {
    const s = e.source?.id || e.source
    const t = e.target?.id || e.target
    return linked.has(s) && linked.has(t) ? 1 : 0.04
  })
}

function resetHighlight() {
  if (nodeGroup)     nodeGroup.attr('opacity', 1)
  if (linkSelection) linkSelection.attr('opacity', d => d.type === 'finding-related' ? 0.55 : 0.5)
}

// ── Exportación ───────────────────────────────────────────────────────────────

/** Convierte el SVG actual a un HTMLCanvasElement de alta resolución,
 *  ignorando el zoom/pan actual y capturando TODOS los nodos del grafo. */
async function svgToCanvas(scale = 2) {
  const svg = svgRef.value
  if (!svg) throw new Error('SVG no disponible')

  // 1. Obtener el grupo de zoom (.zoom-layer) y guardar su transform actual
  const zoomLayer = svg.querySelector('.zoom-layer')
  if (!zoomLayer) throw new Error('No se encontró el layer del grafo')

  const savedTransform = zoomLayer.getAttribute('transform') || ''

  // 2. Resetear temporalmente el transform para medir el bounding box real
  zoomLayer.setAttribute('transform', '')
  const bbox = zoomLayer.getBBox()  // { x, y, width, height } en coordenadas del SVG sin transform
  zoomLayer.setAttribute('transform', savedTransform)  // restaurar inmediatamente

  // Si el grafo no tiene contenido visible, usar dimensiones del SVG
  const PADDING = 60
  const contentW = bbox.width  > 0 ? bbox.width  : (parseInt(svg.getAttribute('width')  || 960))
  const contentH = bbox.height > 0 ? bbox.height : (parseInt(svg.getAttribute('height') || 640))
  const exportW  = Math.ceil(contentW + PADDING * 2)
  const exportH  = Math.ceil(contentH + PADDING * 2)
  const vbX      = bbox.width  > 0 ? bbox.x - PADDING : 0
  const vbY      = bbox.height > 0 ? bbox.y - PADDING : 0

  // 3. Clonar el zoom-layer SIN el transform (para que aparezca en posición natural)
  const cloneLayer = zoomLayer.cloneNode(true)
  cloneLayer.setAttribute('transform', '')

  // 4. Construir un SVG de exportación limpio con las dimensiones del contenido real
  const exportSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  exportSvg.setAttribute('xmlns',       'http://www.w3.org/2000/svg')
  exportSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
  exportSvg.setAttribute('width',       String(exportW))
  exportSvg.setAttribute('height',      String(exportH))
  exportSvg.setAttribute('viewBox',     `${vbX} ${vbY} ${exportW} ${exportH}`)

  // Fondo oscuro
  const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
  bg.setAttribute('x',      String(vbX))
  bg.setAttribute('y',      String(vbY))
  bg.setAttribute('width',  String(exportW))
  bg.setAttribute('height', String(exportH))
  bg.setAttribute('fill',   '#0a0e16')
  exportSvg.appendChild(bg)

  // Copiar los <defs> originales (marcadores de flechas)
  const origDefs = svg.querySelector('defs')
  if (origDefs) exportSvg.appendChild(origDefs.cloneNode(true))

  // Agregar el contenido del grafo
  exportSvg.appendChild(cloneLayer)

  // 5. Serializar → Blob → URL → Image → Canvas
  const svgStr = new XMLSerializer().serializeToString(exportSvg)
  const blob   = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' })
  const url    = URL.createObjectURL(blob)

  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const canvas  = document.createElement('canvas')
      canvas.width  = exportW * scale
      canvas.height = exportH * scale
      const ctx = canvas.getContext('2d')
      ctx.scale(scale, scale)
      ctx.fillStyle = '#0a0e16'
      ctx.fillRect(0, 0, exportW, exportH)
      ctx.drawImage(img, 0, 0, exportW, exportH)
      URL.revokeObjectURL(url)
      resolve({ canvas, W: exportW, H: exportH })
    }
    img.onerror = reject
    img.src = url
  })
}


async function exportPNG() {
  exporting.value    = 'png'
  showExportMenu.value = false
  try {
    const { canvas } = await svgToCanvas(2)
    canvas.toBlob(blob => {
      const a    = document.createElement('a')
      a.href     = URL.createObjectURL(blob)
      a.download = `mapa-trazabilidad-${props.auditId}.png`
      a.click()
      setTimeout(() => URL.revokeObjectURL(a.href), 1500)
    }, 'image/png')
  } catch (e) {
    console.error('Error exportando PNG:', e)
  } finally {
    exporting.value = null
  }
}

async function exportPDF() {
  exporting.value    = 'pdf'
  showExportMenu.value = false
  try {
    const { canvas, W, H } = await svgToCanvas(2)
    const dataUrl = canvas.toDataURL('image/png')

    // Abrir nueva ventana con la imagen y activar impresión del navegador
    const win = window.open('', '_blank')
    if (!win) { alert('Habilita las ventanas emergentes para exportar PDF'); return }

    const auditLabel = props.auditId
    const now = new Date().toLocaleString('es-BO', {
      timeZone: 'America/La_Paz', day: '2-digit', month: 'short',
      year: 'numeric', hour: '2-digit', minute: '2-digit'
    })
    win.document.write(`<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Mapa de Trazabilidad · ${auditLabel}</title>
  <style>
    @page { margin: 12mm; size: landscape; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Inter, system-ui, sans-serif; background: #fff; color: #111; }
    .cover { padding: 16px 20px 12px; border-bottom: 2px solid #e5e7eb; margin-bottom: 14px; }
    .cover h1 { font-size: 18px; font-weight: 700; color: #111827; }
    .cover p  { font-size: 11px; color: #6b7280; margin-top: 3px; }
    .graph-img { width: 100%; height: auto; display: block; }
    .footer { margin-top: 10px; font-size: 9px; color: #9ca3af; text-align: right; padding: 0 4px; }
    @media print {
      .cover { break-after: avoid; }
      .graph-img { max-height: 95vh; object-fit: contain; }
    }
  </style>
</head>
<body>
  <div class="cover">
    <h1>Mapa de Trazabilidad Normativa</h1>
    <p>Auditoría: ${auditLabel} · Exportado: ${now}</p>
  </div>
  <img class="graph-img" src="${dataUrl}" alt="Grafo de trazabilidad" />
  <div class="footer">SAAM · Sistema de Auditoría Automatizada Multimarco</div>
  <script>window.onload = function(){ setTimeout(function(){ window.print() }, 600); }<\/script>
</body></html>`)
    win.document.close()
  } catch (e) {
    console.error('Error exportando PDF:', e)
  } finally {
    exporting.value = null
  }
}

function exportJSON() {
  showExportMenu.value = false
  if (!graphData.value) return
  const payload = {
    auditId:     props.auditId,
    exportedAt:  new Date().toISOString(),
    stats:       graphData.value.stats,
    nodes:       graphData.value.nodes.map(n => ({ ...n })),
    edges:       graphData.value.edges.map(e => ({
      source: e.source?.id ?? e.source,
      target: e.target?.id ?? e.target,
      type:   e.type,
      ...(e.reason     ? { reason:     e.reason }     : {}),
      ...(e.sharedCodes? { sharedCodes: e.sharedCodes } : {}),
      ...(e.similarity ? { similarity:  e.similarity }  : {}),
    })),
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const a    = document.createElement('a')
  a.href     = URL.createObjectURL(blob)
  a.download = `mapa-trazabilidad-${props.auditId}.json`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1500)
}

// ── Watchers ──────────────────────────────────────────────────────────────────
watch([filterFramework, showRelated], () => {
  if (graphData.value) renderGraph(graphData.value)
})

onMounted(() => {
  loadGraph()
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      if (graphData.value) renderGraph(graphData.value)
    })
    resizeObserver.observe(containerRef.value)
  }
  // Cerrar menú de exportación al hacer clic fuera
  document.addEventListener('mousedown', onDocClick)
})

function onDocClick(e) {
  if (exportWrapperRef.value && !exportWrapperRef.value.contains(e.target)) {
    showExportMenu.value = false
  }
}

onUnmounted(() => {
  if (simulation) simulation.stop()
  resizeObserver?.disconnect()
  document.removeEventListener('mousedown', onDocClick)
})
</script>

<template>
  <div class="graph-wrapper">
    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <div class="graph-header">
      <div class="graph-title-area">
        <div class="graph-icon-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
          </svg>
        </div>
        <div>
          <div class="graph-title">Mapa de Trazabilidad Normativa</div>
          <div class="graph-subtitle">Marcos → Normas → Hallazgos → Documentos</div>
        </div>
      </div>

      <div class="graph-controls">
        <label class="control-label">Marco:</label>
        <div class="fw-filter-group">
          <button v-for="fw in ['all','COBIT','COSO','RGSI']" :key="fw"
            class="fw-btn" :class="[{ active: filterFramework === fw }, `fw-${fw.toLowerCase()}`]"
            @click="filterFramework = fw">
            {{ fw === 'all' ? 'Todos' : fw }}
          </button>
        </div>

        <!-- Toggle: relaciones entre hallazgos -->
        <button class="related-toggle" :class="{ active: showRelated }" @click="showRelated = !showRelated">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
          </svg>
          Relaciones
        </button>

        <button class="btn-reload" @click="loadGraph" title="Recargar">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        </button>

        <!-- ── Exportar ──────────────────────────── -->
        <div class="export-wrapper" ref="exportWrapperRef">
          <button
            class="btn-export"
            :class="{ busy: exporting }"
            :disabled="!!exporting || !graphData?.nodes?.length"
            @click="showExportMenu = !showExportMenu"
          >
            <svg v-if="!exporting" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            <div v-else class="export-spinner"/>
            {{ exporting ? `Exportando ${exporting.toUpperCase()}…` : 'Exportar' }}
            <svg v-if="!exporting" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>

          <Transition name="menu-fade">
            <div v-if="showExportMenu" class="export-menu">
              <button class="export-option" @click="exportPNG">
                <div class="export-opt-icon png-icon">PNG</div>
                <div>
                  <div class="export-opt-label">Imagen PNG</div>
                  <div class="export-opt-desc">Alta resolución · fondo oscuro</div>
                </div>
              </button>
              <button class="export-option" @click="exportPDF">
                <div class="export-opt-icon pdf-icon">PDF</div>
                <div>
                  <div class="export-opt-label">Documento PDF</div>
                  <div class="export-opt-desc">Abre diálogo de impresión</div>
                </div>
              </button>
              <div class="export-divider"/>
              <button class="export-option" @click="exportJSON">
                <div class="export-opt-icon json-icon">{}</div>
                <div>
                  <div class="export-opt-label">Datos JSON</div>
                  <div class="export-opt-desc">Nodos, aristas y estadísticas</div>
                </div>
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- ── Stats bar ──────────────────────────────────────────────────────── -->
    <div class="stats-bar">
      <div class="stat-item cobit-color">
        <span class="stat-dot" style="background:#f59e0b"/>
        <strong>{{ stats.cobit_norms }}</strong>
        <span>COBIT</span>
      </div>
      <div class="stat-sep">·</div>
      <div class="stat-item coso-color">
        <span class="stat-dot" style="background:#8b5cf6"/>
        <strong>{{ stats.coso_norms }}</strong>
        <span>COSO</span>
      </div>
      <div class="stat-sep">·</div>
      <div class="stat-item rgsi-color">
        <span class="stat-dot" style="background:#06b6d4"/>
        <strong>{{ stats.rgsi_norms }}</strong>
        <span>RGSI</span>
      </div>
      <div class="stat-sep">·</div>
      <div class="stat-item">
        <span class="stat-dot" style="background:#6366f1"/>
        <strong>{{ stats.total_findings }}</strong>
        <span>Hallazgos</span>
      </div>
      <div class="stat-sep">·</div>
      <div class="stat-item">
        <span class="stat-dot" style="background:#22c55e"/>
        <strong>{{ stats.documents_linked }}</strong>
        <span>Documentos</span>
      </div>
      <div class="stat-sep">·</div>
      <div class="stat-item related-color">
        <span class="stat-dot" style="background:#818cf8"/>
        <strong>{{ stats.related_findings }}</strong>
        <span>Relaciones</span>
      </div>
    </div>

    <!-- ── Canvas ─────────────────────────────────────────────────────────── -->
    <div class="graph-canvas" ref="containerRef">
      <div v-if="loading" class="graph-overlay">
        <div class="graph-spinner"/>
        <span>Construyendo mapa de trazabilidad…</span>
      </div>

      <div v-else-if="error" class="graph-overlay">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p>{{ error }}</p>
        <button class="btn-retry" @click="loadGraph">Reintentar</button>
      </div>

      <div v-else-if="!graphData?.nodes?.length" class="graph-overlay">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="var(--text-2)" stroke-width="1">
          <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
        <h3>Sin datos</h3>
        <p>Ejecuta el análisis IA primero.</p>
      </div>

      <svg v-show="!loading && !error && graphData?.nodes?.length"
        ref="svgRef" class="graph-svg"/>
    </div>

    <!-- ── Leyenda ────────────────────────────────────────────────────────── -->
    <div class="graph-legend">
      <div class="legend-row">
        <div class="legend-item">
          <div class="legend-circle" style="background:#f59e0b;box-shadow:0 0 6px rgba(245,158,11,0.5)"/>
          <span>COBIT (hub)</span>
        </div>
        <div class="legend-item">
          <div class="legend-circle" style="background:#8b5cf6;box-shadow:0 0 6px rgba(139,92,246,0.5)"/>
          <span>COSO (hub)</span>
        </div>
        <div class="legend-item">
          <div class="legend-circle" style="background:#06b6d4;box-shadow:0 0 6px rgba(6,182,212,0.5)"/>
          <span>RGSI (hub)</span>
        </div>
        <div class="legend-sep"/>
        <div class="legend-item">
          <div class="legend-circle" style="background:#ef4444"/>
          <span>Hallazgo Alto</span>
        </div>
        <div class="legend-item">
          <div class="legend-circle" style="background:#22c55e"/>
          <span>Documento</span>
        </div>
        <div class="legend-sep"/>
        <div class="legend-item">
          <div class="legend-line" style="background:#6366f1;border-top:2px dashed #818cf8"/>
          <span>Hallazgos relacionados</span>
        </div>
      </div>
      <div class="legend-hint">
        Arrastra nodos · Scroll para zoom · Clic para resaltar conexiones
      </div>
    </div>

    <!-- ── Tooltip ────────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="tooltip.visible && tooltip.node" class="graph-tooltip"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">

        <div class="tt-badge" :class="`tt-${tooltip.node.type}`">
          {{ tooltip.node.type === 'norm' ? tooltip.node.framework :
             tooltip.node.type === 'framework' ? 'Marco Normativo' :
             tooltip.node.type === 'finding'   ? 'Hallazgo' : 'Documento' }}
        </div>

        <div class="tt-label">{{ tooltip.node.label }}</div>
        <div class="tt-title">{{ tooltip.node.title }}</div>

        <div v-if="tooltip.node.domain"  class="tt-meta">Dominio: {{ tooltip.node.domain }}</div>
        <div v-if="tooltip.node.risk"    class="tt-meta">Riesgo: <strong>{{ tooltip.node.risk }}</strong></div>
        <div v-if="tooltip.node.status"  class="tt-meta">Estado: {{ tooltip.node.status }}</div>
        <div v-if="tooltip.node.page"    class="tt-meta">Página: {{ tooltip.node.page }}</div>
        <div v-if="tooltip.node.docType" class="tt-meta">Tipo: {{ tooltip.node.docType.toUpperCase() }}</div>

        <div class="tt-hint">Clic para resaltar conexiones</div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* ── Layout ───────────────────────────────────────────────────────────────── */
.graph-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 560px;
  background: var(--surface, #111827);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.07);
}

/* ── Header ───────────────────────────────────────────────────────────────── */
.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 18px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(0,0,0,0.25);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.graph-title-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.graph-icon-badge {
  width: 30px; height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1d4ed8, #7c3aed);
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.graph-title   { font-size: 13px; font-weight: 600; color: var(--text, #f9fafb); }
.graph-subtitle { font-size: 10px; color: var(--text-2, #9ca3af); margin-top: 1px; }

/* ── Controls ─────────────────────────────────────────────────────────────── */
.graph-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.control-label { font-size: 11px; color: var(--text-2, #9ca3af); }

.fw-filter-group { display: flex; gap: 2px; }

.fw-btn {
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 10px; font-weight: 600;
  border: 1px solid rgba(255,255,255,0.1);
  background: transparent;
  color: var(--text-2, #9ca3af);
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.04em;
}
.fw-btn:hover { background: rgba(255,255,255,0.07); color: #fff; }
.fw-btn.active { background: rgba(255,255,255,0.1); color: #fff; border-color: rgba(255,255,255,0.2); }
.fw-btn.fw-cobit.active { background: rgba(245,158,11,0.18); border-color: #f59e0b; color: #fcd34d; }
.fw-btn.fw-coso.active  { background: rgba(139,92,246,0.18); border-color: #8b5cf6; color: #c4b5fd; }
.fw-btn.fw-rgsi.active  { background: rgba(6,182,212,0.18);  border-color: #06b6d4; color: #67e8f9; }

.related-toggle {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 9px;
  border-radius: 5px;
  font-size: 10px; font-weight: 500;
  border: 1px solid rgba(99,102,241,0.3);
  background: transparent;
  color: var(--text-2, #9ca3af);
  cursor: pointer;
  transition: all 0.15s;
}
.related-toggle:hover, .related-toggle.active {
  background: rgba(99,102,241,0.15);
  color: #a5b4fc;
  border-color: #6366f1;
}

.btn-reload {
  width: 26px; height: 26px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.1);
  background: transparent;
  color: var(--text-2, #9ca3af);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.btn-reload:hover { background: rgba(255,255,255,0.07); color: #fff; }

/* ── Stats bar ────────────────────────────────────────────────────────────── */
.stats-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 18px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  background: rgba(0,0,0,0.15);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--text-2, #9ca3af);
}
.stat-item strong { color: var(--text, #f9fafb); font-variant-numeric: tabular-nums; }
.stat-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.stat-sep { color: rgba(255,255,255,0.12); font-size: 10px; }
.related-color { color: #a5b4fc; }
.related-color strong { color: #818cf8; }

/* ── Canvas ───────────────────────────────────────────────────────────────── */
.graph-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  min-height: 380px;
  background: radial-gradient(ellipse at 50% 40%, rgba(17,24,39,0.97) 0%, rgba(9,11,18,0.99) 100%);
}

.graph-svg { width: 100%; height: 100%; display: block; cursor: grab; }
.graph-svg:active { cursor: grabbing; }

/* ── Overlay states ───────────────────────────────────────────────────────── */
.graph-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 10px;
  color: var(--text-2, #9ca3af);
  font-size: 12px;
}
.graph-overlay h3 { font-size: 14px; font-weight: 600; color: var(--text, #f9fafb); margin: 0; }
.graph-overlay p  { margin: 0; text-align: center; max-width: 220px; }
.graph-spinner {
  width: 30px; height: 30px;
  border: 2px solid rgba(255,255,255,0.07);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.btn-retry {
  padding: 5px 14px;
  border-radius: 6px;
  border: 1px solid rgba(239,68,68,0.4);
  background: rgba(239,68,68,0.1);
  color: #fca5a5;
  font-size: 11px;
  cursor: pointer;
}

/* ── Legend ───────────────────────────────────────────────────────────────── */
.graph-legend {
  padding: 8px 18px;
  border-top: 1px solid rgba(255,255,255,0.05);
  background: rgba(0,0,0,0.2);
  flex-shrink: 0;
}
.legend-row {
  display: flex; align-items: center; gap: 12px;
  flex-wrap: wrap;
}
.legend-item { display: flex; align-items: center; gap: 5px; }
.legend-item span { font-size: 10px; color: var(--text-2, #9ca3af); }
.legend-circle { width: 10px; height: 10px; border-radius: 50%; }
.legend-line { width: 22px; height: 0; border-top: 2px dashed #818cf8; }
.legend-sep { width: 1px; height: 14px; background: rgba(255,255,255,0.08); }
.legend-hint {
  margin-top: 5px;
  font-size: 9px;
  color: rgba(156,163,175,0.5);
  font-style: italic;
}

/* ── Tooltip ──────────────────────────────────────────────────────────────── */
.graph-tooltip {
  position: fixed;
  z-index: 9999;
  background: rgba(10,14,22,0.97);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 10px 14px;
  min-width: 170px; max-width: 250px;
  pointer-events: none;
  backdrop-filter: blur(14px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.55);
}
.tt-badge {
  font-size: 9px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
  margin-bottom: 5px;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}
.tt-framework { background: rgba(99,102,241,0.2); color: #a5b4fc; }
.tt-norm      { background: rgba(245,158,11,0.15); color: #fcd34d; }
.tt-finding   { background: rgba(239,68,68,0.15);  color: #fca5a5; }
.tt-document  { background: rgba(34,197,94,0.15);  color: #86efac; }

.tt-label { font-size: 13px; font-weight: 600; color: #f9fafb; font-family: 'Courier New', monospace; margin-bottom: 2px; }
.tt-title { font-size: 11px; color: #d1d5db; line-height: 1.4; margin-bottom: 6px; }
.tt-meta  { font-size: 10px; color: #9ca3af; margin-bottom: 2px; }
.tt-meta strong { color: #f9fafb; }
.tt-hint  { font-size: 9px; color: rgba(156,163,175,0.5); margin-top: 6px; font-style: italic; }

/* ── Export button & menu ─────────────────────────────────────────────────── */
.export-wrapper { position: relative; }

.btn-export {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px; font-weight: 500;
  border: 1px solid rgba(99,102,241,0.4);
  background: rgba(99,102,241,0.1);
  color: #a5b4fc;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.btn-export:hover:not(:disabled) {
  background: rgba(99,102,241,0.2);
  border-color: #6366f1;
  color: #c7d2fe;
}
.btn-export:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-export.busy { pointer-events: none; }

.export-spinner {
  width: 11px; height: 11px;
  border: 1.5px solid rgba(165,180,252,0.3);
  border-top-color: #a5b4fc;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.export-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: rgba(10,14,25,0.98);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 6px;
  min-width: 210px;
  z-index: 1000;
  backdrop-filter: blur(16px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.6);
}

.export-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border-radius: 7px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
}
.export-option:hover { background: rgba(255,255,255,0.06); }

.export-opt-icon {
  width: 34px; height: 34px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 700; letter-spacing: 0.03em;
  flex-shrink: 0;
}
.png-icon  { background: rgba(34,197,94,0.15);  color: #86efac; border: 1px solid rgba(34,197,94,0.25); }
.pdf-icon  { background: rgba(239,68,68,0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }
.json-icon { background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.25); font-size: 12px; }

.export-opt-label { font-size: 12px; font-weight: 500; color: #f9fafb; margin-bottom: 1px; }
.export-opt-desc  { font-size: 10px; color: #6b7280; }

.export-divider {
  height: 1px;
  background: rgba(255,255,255,0.06);
  margin: 4px 6px;
}

.menu-fade-enter-active, .menu-fade-leave-active { transition: opacity 0.12s, transform 0.12s; }
.menu-fade-enter-from, .menu-fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
