import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import type { EnrichedEntity, Scene } from '../hooks'
import type { ProjectSummary } from '../types'
import { formatEntityName } from '../utils'

// Helpers

function addHeader(doc: jsPDF, text: string, y: number = 20) {
  doc.setFontSize(18)
  doc.text(text, 14, y)
  doc.setFontSize(12)
  return y + 10
}

function addMetadata(doc: jsPDF, label: string, value: string | number | undefined, y: number): number {
  if (!value) return y
  doc.setFont('helvetica', 'bold')
  doc.text(`${label}:`, 14, y)
  doc.setFont('helvetica', 'normal')
  doc.text(`${value}`, 50, y)
  return y + 7
}

// Call Sheet Logic

interface CallSheetData {
  productionName: string
  date: string
  scenes: Scene[]
  characters: EnrichedEntity[]
  locations: EnrichedEntity[]
}

function generateCallSheetPDF(doc: jsPDF, data: CallSheetData) {
  let y = 20
  
  // Header
  doc.setFontSize(22)
  doc.text('CALL SHEET', 105, y, { align: 'center' })
  y += 15
  
  doc.setFontSize(12)
  y = addMetadata(doc, 'Production', data.productionName, y)
  y = addMetadata(doc, 'Date', data.date, y)
  y += 10
  
  // Group scenes by location
  const scenesByLocation = new Map<string, Scene[]>()
  data.scenes.forEach(scene => {
    const loc = scene.location || 'Unknown'
    if (!scenesByLocation.has(loc)) {
      scenesByLocation.set(loc, [])
    }
    scenesByLocation.get(loc)!.push(scene)
  })

  autoTable(doc, {
    startY: y,
    head: [['Scene', 'Set', 'Desc', 'Cast', 'Pages']],
    body: data.scenes.map(scene => [
      scene.index,
      scene.intExt + ' ' + scene.location,
      scene.summary,
      'TBD', // We need cast per scene, which is complex to derive without full breakdown data linked here
      '1/8' // Placeholder
    ]),
    theme: 'grid',
    styles: { fontSize: 10 },
    headStyles: { fillColor: [41, 128, 185] }
  })
}

// Export Functions

export function exportProjectPDF(
  project: ProjectSummary | undefined,
  scenes: Scene[],
  characters: EnrichedEntity[],
  locations: EnrichedEntity[],
  props: EnrichedEntity[]
) {
  const doc = new jsPDF()
  let y = 20
  
  // Title Page
  if (project) {
    doc.setFontSize(24)
    doc.text(project.display_name, 105, 100, { align: 'center' })
    doc.setFontSize(14)
    doc.text(`Project ID: ${project.project_id}`, 105, 115, { align: 'center' })
    doc.addPage()
  }
  
  // Scenes
  y = addHeader(doc, 'Scenes', 20)
  autoTable(doc, {
    startY: y,
    head: [['#', 'Slugline', 'Time', 'Summary']],
    body: scenes.map(s => [
      s.index,
      `${s.intExt} ${s.location}`,
      s.timeOfDay,
      s.summary.substring(0, 50) + (s.summary.length > 50 ? '...' : '')
    ]),
  })
  
  // Characters
  doc.addPage()
  y = addHeader(doc, 'Characters', 20)
  autoTable(doc, {
    startY: y,
    head: [['Name', 'Scenes', 'First Scene', 'Description']],
    body: characters.map(c => [
      formatEntityName(c.entity_id!),
      c.sceneCount,
      c.firstSceneNumber || '-',
      (c.description || '').substring(0, 50) + ((c.description?.length || 0) > 50 ? '...' : '')
    ]),
  })
  
  // Locations
  doc.addPage()
  y = addHeader(doc, 'Locations', 20)
  autoTable(doc, {
    startY: y,
    head: [['Name', 'Scenes', 'Description']],
    body: locations.map(l => [
      formatEntityName(l.entity_id!),
      l.sceneCount,
      (l.description || '').substring(0, 50) + ((l.description?.length || 0) > 50 ? '...' : '')
    ]),
  })

  // Props
  doc.addPage()
  y = addHeader(doc, 'Props', 20)
  autoTable(doc, {
    startY: y,
    head: [['Name', 'Scenes', 'Description']],
    body: props.map(p => [
      formatEntityName(p.entity_id!),
      p.sceneCount,
      (p.description || '').substring(0, 50) + ((p.description?.length || 0) > 50 ? '...' : '')
    ]),
  })
  
  doc.save(`${project?.display_name || 'project'}-export.pdf`)
}

export function exportCallSheet(
  project: ProjectSummary | undefined,
  scenes: Scene[],
  characters: EnrichedEntity[],
  locations: EnrichedEntity[]
) {
  const doc = new jsPDF()
  generateCallSheetPDF(doc, {
    productionName: project?.display_name || 'Untitled Production',
    date: new Date().toLocaleDateString(),
    scenes,
    characters,
    locations
  })
  doc.save('call-sheet.pdf')
}
