<template>
    <div class="export-timetable-container">
        <div class="export-header">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">
                {{ $t('export.title') }}
            </h3>
            <p class="text-sm text-gray-600 mb-4">
                {{ $t('export.description') }}
            </p>
        </div>

        <!-- Export Mode Selection -->
        <div class="export-mode-selection mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-3">
                {{ $t('export.mode.label') }}
            </label>
            <div class="flex gap-4">
                <label class="flex items-center">
                    <input v-model="exportMode" type="radio" value="merged"
                        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
                    <span class="ml-2 text-sm text-gray-700">{{ $t('export.mode.merged') }}</span>
                </label>
                <label class="flex items-center">
                    <input v-model="exportMode" type="radio" value="individual"
                        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
                    <span class="ml-2 text-sm text-gray-700">{{ $t('export.mode.individual') }}</span>
                </label>
            </div>
            <p class="text-xs text-gray-500 mt-2">
                {{ exportMode === 'merged' ? $t('export.mode.mergedDescription') :
                    $t('export.mode.individualDescription') }}
            </p>
        </div>

        <div class="export-options">
            <button @click="exportToTxt" :disabled="!hasSelectedParticipants" class="export-button txt-export"
                :class="{ 'disabled': !hasSelectedParticipants }">
                <DocumentTextIcon class="h-5 w-5" />
                <span>{{ $t('export.formats.txt') }}</span>
            </button>

            <button @click="exportToPdf" :disabled="!hasSelectedParticipants" class="export-button pdf-export"
                :class="{ 'disabled': !hasSelectedParticipants }">
                <DocumentIcon class="h-5 w-5" />
                <span>{{ $t('export.formats.pdf') }}</span>
            </button>

            <button @click="exportToExcel" :disabled="!hasSelectedParticipants" class="export-button excel-export"
                :class="{ 'disabled': !hasSelectedParticipants }">
                <TableCellsIcon class="h-5 w-5" />
                <span>{{ $t('export.formats.excel') }}</span>
            </button>
        </div>

        <div v-if="!hasSelectedParticipants" class="export-warning">
            <ExclamationTriangleIcon class="h-4 w-4 text-amber-500" />
            <span class="text-sm text-amber-700">{{ $t('export.warning.noSelection') }}</span>
        </div>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { DocumentTextIcon, DocumentIcon, TableCellsIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import jsPDF from 'jspdf'
import * as XLSX from 'xlsx'
import JSZip from 'jszip'
import anyAscii from 'any-ascii'

const props = defineProps({
    selectedParticipants: {
        type: Array,
        required: true
    },
    participants: {
        type: Array,
        required: true
    }
})

const exportMode = ref('merged')

const hasSelectedParticipants = computed(() => {
    return props.selectedParticipants.length > 0
})

const getSelectedParticipantsData = () => {
    return props.participants.filter(p => props.selectedParticipants.includes(p.name))
}

const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    })
}

const mapToAscii = (text) => {
    if (!text) return ''
    return anyAscii(text)
}

const generateTxtContent = (participant) => {
    let content = `PARTICIPANT: ${participant.name.toUpperCase()}\n`
    content += `WORKLOAD: ${participant.workload}\n`
    content += `TOTAL HOURS: ${participant.totalHours}h\n`
    content += `TOTAL TASKS: ${participant.assignments.length}\n`
    content += '-'.repeat(40) + '\n\n'

    if (participant.assignments.length > 0) {
        content += 'SCHEDULE:\n'
        participant.assignments.forEach((assignment, index) => {
            content += `${index + 1}. ${assignment.task_description}\n`
            content += `   Date: ${formatDate(assignment.date)}\n`
            content += `   Duration: ${assignment.duration}\n`
            content += `   Hours: ${assignment.total_hours}h\n`
            if (assignment.location) {
                content += `   Location: ${assignment.location}\n`
            }
            content += '\n'
        })
    } else {
        content += 'No assignments scheduled.\n'
    }
    return content
}

const exportToTxt = async () => {
    if (!hasSelectedParticipants.value) return

    const selectedData = getSelectedParticipantsData()

    if (exportMode.value === 'merged') {
        // Merged export - single file with all participants
        let content = 'PARTICIPANT TIMETABLES\n'
        content += '='.repeat(50) + '\n\n'

        selectedData.forEach(participant => {
            content += generateTxtContent(participant)
            content += '\n' + '='.repeat(50) + '\n\n'
        })

        // Create and download file
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `participant_timetables_${new Date().toISOString().split('T')[0]}.txt`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
    } else {
        // Individual export - ZIP file with separate files for each participant
        const zip = new JSZip()

        selectedData.forEach(participant => {
            const content = generateTxtContent(participant)
            const fileName = `${mapToAscii(participant.name).replace(/[^a-zA-Z0-9]/g, '_')}_timetable.txt`
            zip.file(fileName, content)
        })

        const zipBlob = await zip.generateAsync({ type: 'blob' })
        const url = URL.createObjectURL(zipBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `participant_timetables_${new Date().toISOString().split('T')[0]}.zip`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
    }
}

const generatePdfForParticipant = (participant) => {
    const pdf = new jsPDF()
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    let yPosition = 20
    const lineHeight = 7
    const margin = 20

    // Helper function to add text with word wrap
    const addText = (text, x, y, maxWidth = pageWidth - 2 * margin) => {
        const lines = pdf.splitTextToSize(text, maxWidth)
        pdf.text(lines, x, y)
        return y + (lines.length * lineHeight)
    }

    // Helper function to check if we need a new page
    const checkNewPage = (requiredSpace) => {
        if (yPosition + requiredSpace > pageHeight - margin) {
            pdf.addPage()
            yPosition = 20
            return true
        }
        return false
    }

    // Title
    pdf.setFontSize(16)
    pdf.setFont(undefined, 'bold')
    yPosition = addText(`PARTICIPANT: ${participant.name.toUpperCase()}`, margin, yPosition)

    // Participant info
    pdf.setFontSize(12)
    pdf.setFont(undefined, 'normal')
    yPosition += 5
    yPosition = addText(`Workload: ${participant.workload}`, margin, yPosition)
    yPosition = addText(`Total Hours: ${participant.totalHours}h`, margin, yPosition)
    yPosition = addText(`Total Tasks: ${participant.assignments.length}`, margin, yPosition)

    yPosition += 10

    // Schedule section
    if (participant.assignments.length > 0) {
        pdf.setFont(undefined, 'bold')
        yPosition = addText('SCHEDULE:', margin, yPosition)
        pdf.setFont(undefined, 'normal')
        yPosition += 5

        participant.assignments.forEach((assignment, index) => {
            checkNewPage(30) // Reserve space for assignment details

            const assignmentText = `${index + 1}. ${assignment.task_description}`
            yPosition = addText(assignmentText, margin, yPosition)

            yPosition = addText(`   Date: ${formatDate(assignment.date)}`, margin, yPosition)
            yPosition = addText(`   Duration: ${assignment.duration}`, margin, yPosition)
            yPosition = addText(`   Hours: ${assignment.total_hours}h`, margin, yPosition)

            if (assignment.location) {
                yPosition = addText(`   Location: ${assignment.location}`, margin, yPosition)
            }

            yPosition += 5
        })
    } else {
        pdf.setFont(undefined, 'italic')
        yPosition = addText('No assignments scheduled.', margin, yPosition)
    }

    return pdf
}

const exportToPdf = async () => {
    if (!hasSelectedParticipants.value) return

    const selectedData = getSelectedParticipantsData()

    if (exportMode.value === 'merged') {
        // Merged export - single PDF with all participants
        const pdf = new jsPDF()
        const pageWidth = pdf.internal.pageSize.getWidth()
        const pageHeight = pdf.internal.pageSize.getHeight()
        let yPosition = 20
        const lineHeight = 7
        const margin = 20

        // Helper function to add text with word wrap
        const addText = (text, x, y, maxWidth = pageWidth - 2 * margin) => {
            const lines = pdf.splitTextToSize(text, maxWidth)
            pdf.text(lines, x, y)
            return y + (lines.length * lineHeight)
        }

        // Helper function to check if we need a new page
        const checkNewPage = (requiredSpace) => {
            if (yPosition + requiredSpace > pageHeight - margin) {
                pdf.addPage()
                yPosition = 20
                return true
            }
            return false
        }

        // Add title
        pdf.setFontSize(18)
        pdf.setFont(undefined, 'bold')
        yPosition = addText('PARTICIPANT TIMETABLES', margin, yPosition)
        yPosition += 20

        selectedData.forEach((participant, participantIndex) => {
            if (participantIndex > 0) {
                pdf.addPage()
                yPosition = 20
            }

            // Participant title
            pdf.setFontSize(16)
            pdf.setFont(undefined, 'bold')
            yPosition = addText(`PARTICIPANT: ${participant.name.toUpperCase()}`, margin, yPosition)

            // Participant info
            pdf.setFontSize(12)
            pdf.setFont(undefined, 'normal')
            yPosition += 5
            yPosition = addText(`Workload: ${participant.workload}`, margin, yPosition)
            yPosition = addText(`Total Hours: ${participant.totalHours}h`, margin, yPosition)
            yPosition = addText(`Total Tasks: ${participant.assignments.length}`, margin, yPosition)

            yPosition += 10

            // Schedule section
            if (participant.assignments.length > 0) {
                pdf.setFont(undefined, 'bold')
                yPosition = addText('SCHEDULE:', margin, yPosition)
                pdf.setFont(undefined, 'normal')
                yPosition += 5

                participant.assignments.forEach((assignment, index) => {
                    checkNewPage(30) // Reserve space for assignment details

                    const assignmentText = `${index + 1}. ${assignment.task_description}`
                    yPosition = addText(assignmentText, margin, yPosition)

                    yPosition = addText(`   Date: ${formatDate(assignment.date)}`, margin, yPosition)
                    yPosition = addText(`   Duration: ${assignment.duration}`, margin, yPosition)
                    yPosition = addText(`   Hours: ${assignment.total_hours}h`, margin, yPosition)

                    if (assignment.location) {
                        yPosition = addText(`   Location: ${assignment.location}`, margin, yPosition)
                    }

                    yPosition += 5
                })
            } else {
                pdf.setFont(undefined, 'italic')
                yPosition = addText('No assignments scheduled.', margin, yPosition)
            }
        })

        // Save the PDF
        pdf.save(`participant_timetables_${new Date().toISOString().split('T')[0]}.pdf`)
    } else {
        // Individual export - ZIP file with separate PDFs for each participant
        const zip = new JSZip()

        for (const participant of selectedData) {
            const pdf = generatePdfForParticipant(participant)
            const pdfOutput = pdf.output('blob')
            const fileName = `${mapToAscii(participant.name).replace(/[^a-zA-Z0-9]/g, '_')}_timetable.pdf`
            zip.file(fileName, pdfOutput)
        }

        const zipBlob = await zip.generateAsync({ type: 'blob' })
        const url = URL.createObjectURL(zipBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `participant_timetables_${new Date().toISOString().split('T')[0]}.zip`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
    }
}

const exportToExcel = async () => {
    if (!hasSelectedParticipants.value) return

    const selectedData = getSelectedParticipantsData()

    if (exportMode.value === 'merged') {
        // Merged export - single Excel file with multiple sheets
        const workbook = XLSX.utils.book_new()

        // Create a summary sheet
        const summaryData = [
            ['Participant', 'Workload', 'Total Hours', 'Total Tasks'],
            ...selectedData.map(p => [p.name, p.workload, p.totalHours, p.assignments.length])
        ]
        const summarySheet = XLSX.utils.aoa_to_sheet(summaryData)
        XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary')

        // Create detailed sheets for each participant
        selectedData.forEach(participant => {
            const participantData = [
                ['Task Description', 'Date', 'Duration', 'Hours', 'Location'],
                ...participant.assignments.map(assignment => [
                    assignment.task_description,
                    formatDate(assignment.date),
                    assignment.duration,
                    assignment.total_hours,
                    assignment.location || ''
                ])
            ]

            const participantSheet = XLSX.utils.aoa_to_sheet(participantData)
            const sheetName = mapToAscii(participant.name).replace(/[^a-zA-Z0-9]/g, '').substring(0, 31) // Excel sheet name limit
            XLSX.utils.book_append_sheet(workbook, participantSheet, sheetName)
        })

        // Save the Excel file
        XLSX.writeFile(workbook, `participant_timetables_${new Date().toISOString().split('T')[0]}.xlsx`)
    } else {
        // Individual export - ZIP file with separate Excel files for each participant
        const zip = new JSZip()

        for (const participant of selectedData) {
            const workbook = XLSX.utils.book_new()

            // Create summary sheet for this participant
            const summaryData = [
                ['Participant', 'Workload', 'Total Hours', 'Total Tasks'],
                [participant.name, participant.workload, participant.totalHours, participant.assignments.length]
            ]
            const summarySheet = XLSX.utils.aoa_to_sheet(summaryData)
            XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary')

            // Create detailed sheet for this participant
            const participantData = [
                ['Task Description', 'Date', 'Duration', 'Hours', 'Location'],
                ...participant.assignments.map(assignment => [
                    assignment.task_description,
                    formatDate(assignment.date),
                    assignment.duration,
                    assignment.total_hours,
                    assignment.location || ''
                ])
            ]

            const participantSheet = XLSX.utils.aoa_to_sheet(participantData)
            XLSX.utils.book_append_sheet(workbook, participantSheet, 'Schedule')

            // Convert workbook to buffer
            const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
            const fileName = `${mapToAscii(participant.name).replace(/[^a-zA-Z0-9]/g, '_')}_timetable.xlsx`
            zip.file(fileName, excelBuffer)
        }

        const zipBlob = await zip.generateAsync({ type: 'blob' })
        const url = URL.createObjectURL(zipBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `participant_timetables_${new Date().toISOString().split('T')[0]}.zip`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
    }
}
</script>

<style scoped>
.export-timetable-container {
    @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.export-header {
    @apply mb-6;
}

.export-mode-selection {
    @apply bg-gray-50 rounded-lg p-4 border border-gray-200;
}

.export-options {
    @apply flex flex-wrap gap-3 mb-4;
}

.export-button {
    @apply flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-200 font-medium text-sm;
}

.export-button:not(.disabled) {
    @apply hover:shadow-md transform hover:-translate-y-0.5;
}

.export-button.disabled {
    @apply opacity-50 cursor-not-allowed;
}

.txt-export {
    @apply bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100;
}

.txt-export:not(.disabled):hover {
    @apply bg-gray-100 border-gray-400;
}

.pdf-export {
    @apply bg-red-50 border-red-300 text-red-700 hover:bg-red-100;
}

.pdf-export:not(.disabled):hover {
    @apply bg-red-100 border-red-400;
}

.excel-export {
    @apply bg-green-50 border-green-300 text-green-700 hover:bg-green-100;
}

.excel-export:not(.disabled):hover {
    @apply bg-green-100 border-green-400;
}

.export-warning {
    @apply flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg;
}
</style>