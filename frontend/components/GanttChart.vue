<template>
  <div class="gantt-chart">
    <div class="mb-4">
      <h2 class="text-xl font-semibold text-gray-800 mb-2">{{ $t('gantt.title') }}</h2>
      <p class="text-sm text-gray-600">{{ $t('gantt.title') }}</p>
    </div>

    <!-- Gantt Chart for Selected Participants -->
    <div class="mb-6 p-4 bg-gray-50 rounded-lg">
      <h3 class="text-lg font-medium mb-3">{{ $t('gantt.title') }}</h3>
      <g-gantt-chart :chart-start="chartStart" :chart-end="chartEnd" :precision="precision" bar-start="startDateTime"
        bar-end="endDateTime" :bar-tooltip="true" :width="chartWidth">
        <g-gantt-row v-for="participant in displayedParticipants" :key="participant.name" :label="participant.name"
          :bars="getParticipantBars(participant.name)" :bar-tooltip="true" :highlight-on-hover="true" />
      </g-gantt-chart>
    </div>

    <!-- Legend -->
    <div class="mt-6 pt-4 border-t border-gray-200">
      <h3 class="text-sm font-medium text-gray-700 mb-3">{{ $t('gantt.title') }} - {{ $t('participants.workload.filter') }}</h3>
      <div class="flex flex-wrap gap-4 text-xs">
        <div class="flex items-center">
          <div class="w-4 h-4 bg-red-500 rounded mr-2"></div>
          <span>{{ $t('participants.workload.high') }}</span>
        </div>
        <div class="flex items-center">
          <div class="w-4 h-4 bg-amber-500 rounded mr-2"></div>
          <span>{{ $t('participants.workload.medium') }}</span>
        </div>
        <div class="flex items-center">
          <div class="w-4 h-4 bg-green-500 rounded mr-2"></div>
          <span>{{ $t('participants.workload.low') }}</span>
        </div>
        <div class="flex items-center">
          <div class="w-4 h-4 bg-purple-500 rounded mr-2"></div>
          <span>SNU</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useAssignments } from '~/composables/useAssignments'

const props = defineProps({
  assignments: {
    type: Array,
    required: true
  },
  participants: {
    type: Array,
    required: true
  }
})


const { getDateRange, processForGantt } = useAssignments()

// Chart configuration
const precision = 'hour'
const chartWidth = 1000

// Debug: Log the processed assignments
const processedAssignments = computed(() => {
  const processed = processForGantt(props.assignments)
  console.log('Processed assignments:', processed)
  return processed
})

// Get displayed participants from props
const displayedParticipants = computed(() => {
  return props.participants || []
})

// Chart date range
const chartStart = computed(() => {
  const dateRange = getDateRange(processedAssignments.value)
  if (!dateRange.start) return new Date().toISOString().slice(0, 16).replace('T', ' ')

  // Start from beginning of the day
  const start = new Date(dateRange.start)
  return start.toISOString().slice(0, 16).replace('T', ' ')
})

const chartEnd = computed(() => {
  const dateRange = getDateRange(processedAssignments.value)
  if (!dateRange.end) return new Date().toISOString().slice(0, 16).replace('T', ' ')

  // End at end of the day
  const end = new Date(dateRange.end)
  end.setHours(23, 59, 59, 999)
  return end.toISOString().slice(0, 16).replace('T', ' ')
})

console.log('Chart start:', chartStart.value)
console.log('Chart end:', chartEnd.value)

// Get bars for a specific participant
const getParticipantBars = (participantName) => {
  const bars = processedAssignments.value
    .filter(a => a.participant === participantName && a.startDateTime && a.endDateTime)
    .map(assignment => {
      // Ensure we have proper Date objects
      const startDate = assignment.startDateTime instanceof Date
        ? assignment.startDateTime
        : new Date(assignment.startDateTime)
      const endDate = assignment.endDateTime instanceof Date
        ? assignment.endDateTime
        : new Date(assignment.endDateTime)

      const startDateTimeStr = startDate.toISOString().slice(0, 16).replace('T', ' ')
      const endDateTimeStr = endDate.toISOString().slice(0, 16).replace('T', ' ')
      console.log(`Assignment ${assignment.task_id}: ${startDateTimeStr} to ${endDateTimeStr}`)

      return {
        startDateTime: startDateTimeStr,
        endDateTime: endDateTimeStr,
        ganttBarConfig: {
          id: `${assignment.task_id}-${assignment.participant}`,
          label: `${assignment.location} - ${assignment.task_description}`,
          hasHandles: true,
          bundle: assignment.task_id,
          style: {
            background: getBarColor(assignment.participant_workload),
            borderRadius: '4px',
            color: 'black',
            fontSize: '12px',
            fontWeight: '500'
          },
          tooltip: {
            html: `
              <div class="p-2">
                <div class="font-semibold">${assignment.task_description}</div>
                <div class="text-sm mt-1">Location: ${assignment.location}</div>
                <div class="text-sm">Duration: ${assignment.duration}</div>
                <div class="text-sm">Workload: ${assignment.participant_workload}</div>
              </div>
            `
          }
        }
      }
    })

  console.log(`Final bars for ${participantName}:`, bars) // Debug log
  return bars
}

// Get bar color based on workload
const getBarColor = (workload) => {
  switch (workload) {
    case 'High':
      return '#EF4444' // red-500 - High workload
    case 'Medium':
      return '#F59E0B' // amber-500 - Medium workload
    case 'Low':
      return '#10B981' // green-500 - Low workload
    case 'SNU':
      return '#8B5CF6' // purple-500 - SNU participants
    default:
      return '#6B7280' // gray-500 - Unknown workload
  }
}
</script>

<style scoped>
.gantt-chart {
  @apply w-full;
}

.gantt-container {
  @apply border border-gray-200 rounded-lg overflow-hidden;
}

/* Custom styles for vue-ganttastic */
:deep(.g-gantt-chart) {
  font-family: inherit;
}

:deep(.g-gantt-row-label) {
  @apply bg-gray-50 border-r border-gray-200 px-3 py-2 text-sm font-medium text-gray-700;
}

:deep(.g-gantt-row) {
  @apply border-b border-gray-100;
}

:deep(.g-gantt-bar) {
  @apply shadow-sm;
}

:deep(.g-gantt-bar:hover) {
  @apply shadow-md;
}

:deep(.g-gantt-chart-header) {
  @apply bg-gray-100 border-b border-gray-200;
}

:deep(.g-gantt-chart-header-cell) {
  @apply px-2 py-1 text-xs font-medium text-gray-600 border-r border-gray-200;
}
</style>
